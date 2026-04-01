#!/usr/bin/env python3
"""
Test script to verify payment system fixes
"""

import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

# Add the project directory to the Python path
sys.path.insert(0, '/Users/arfatulshaikh/Projects/InfoHub/FactoryInfoHub')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from Karkahan.models import Factory, PaymentGateway, Order, OrderItem, Cart, CartItem
from category.models import Category
from location.models import Country, State, City
from django.urls import reverse
from django.core import mail


class PaymentSystemTests(TestCase):
    """Test payment system functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test category
        self.category = Category.objects.create(
            name='Test Category',
            description='Test category for payment testing'
        )
        
        # Create test location
        self.country = Country.objects.create(name='Test Country')
        self.state = State.objects.create(name='Test State', country=self.country)
        self.city = City.objects.create(name='Test City', state=self.state)
        
        # Create test factory
        self.factory = Factory.objects.create(
            name='Test Factory',
            slug='test-factory',
            description='Test factory for payment testing',
            category=self.category,
            country=self.country,
            state=self.state,
            city=self.city,
            price=100.00,
            is_active=True,
            is_verified=True
        )
        
        # Create test payment gateway
        self.gateway = PaymentGateway.objects.create(
            name='stripe',
            is_active=True,
            key_id='test_key_id',
            key_secret='test_key_secret',
            webhook_secret='test_webhook_secret',
            mode='test'
        )
    
    def test_stripe_api_key_retrieval(self):
        """Test that Stripe API key is retrieved correctly from database"""
        from Karkahan.views import get_stripe_api_key, get_stripe_publishable_key
        
        # Test with active Stripe gateway
        api_key = get_stripe_api_key()
        publishable_key = get_stripe_publishable_key()
        
        self.assertEqual(api_key, 'test_key_secret')
        self.assertEqual(publishable_key, 'test_key_id')
        
        # Test with no active gateway
        self.gateway.is_active = False
        self.gateway.save()
        
        api_key = get_stripe_api_key()
        publishable_key = get_stripe_publishable_key()
        
        self.assertIsNone(api_key)
        self.assertIsNone(publishable_key)
    
    def test_razorpay_configuration_validation(self):
        """Test Razorpay configuration validation"""
        # Create Razorpay gateway with missing keys
        razorpay_gateway = PaymentGateway.objects.create(
            name='razorpay',
            is_active=True,
            key_id='',  # Missing key_id
            key_secret='',  # Missing key_secret
            mode='test'
        )
        
        # Test validation in initiate_checkout
        client = Client()
        client.login(username='testuser', password='testpass123')
        
        # Add factory to cart
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, factory=self.factory)
        
        # Try to initiate checkout with incomplete Razorpay config
        response = client.post(reverse('karkahan:initiate_checkout'))
        
        # Should return error for incomplete configuration
        self.assertEqual(response.status_code, 500)
        response_data = response.json()
        self.assertIn('error', response_data)
        self.assertIn('Razorpay configuration incomplete', response_data['error'])
    
    def test_order_creation_and_completion(self):
        """Test order creation and completion workflow"""
        # Create cart and add factory
        cart, _ = Cart.objects.get_or_create(user=self.user)
        CartItem.objects.create(cart=cart, factory=self.factory)
        
        # Create order
        order = Order.objects.create(
            user=self.user,
            total_amount=self.factory.price,
            payment_status='pending',
            gateway_used=self.gateway
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            factory=self.factory,
            price_at_purchase=self.factory.price
        )
        
        # Test order completion
        order.payment_status = 'completed'
        order.save()
        
        # Verify order was completed
        self.assertEqual(order.payment_status, 'completed')
        self.assertTrue(order.payment_completed)
        
        # Verify cart was cleared
        cart.refresh_from_db()
        self.assertEqual(cart.items.count(), 0)
    
    def test_email_template_exists(self):
        """Test that email template exists and is valid"""
        from django.template.loader import render_to_string
        
        # Create a test order
        order = Order.objects.create(
            user=self.user,
            total_amount=self.factory.price,
            payment_status='completed',
            gateway_used=self.gateway
        )
        
        OrderItem.objects.create(
            order=order,
            factory=self.factory,
            price_at_purchase=self.factory.price
        )
        
        # Test email template rendering
        try:
            html_content = render_to_string('emails/order_receipt.html', {
                'user': self.user,
                'order': order,
                'factories': [self.factory],
            })
            
            # Check that template contains expected content
            self.assertIn('Order Receipt', html_content)
            self.assertIn(self.factory.name, html_content)
            self.assertIn(str(order.order_number), html_content)
            self.assertIn(str(self.factory.price), html_content)
            
            print("✓ Email template renders correctly")
            
        except Exception as e:
            self.fail(f"Email template failed to render: {e}")
    
    def test_send_order_receipt_function(self):
        """Test the send_order_receipt function"""
        from Karkahan.views import send_order_receipt
        
        # Create a test order
        order = Order.objects.create(
            user=self.user,
            total_amount=self.factory.price,
            payment_status='completed',
            gateway_used=self.gateway
        )
        
        OrderItem.objects.create(
            order=order,
            factory=self.factory,
            price_at_purchase=self.factory.price
        )
        
        # Clear any existing emails
        mail.outbox = []
        
        # Test email sending
        result = send_order_receipt(self.user, order, [self.factory])
        
        # Check that email was sent
        self.assertTrue(result)
        self.assertEqual(len(mail.outbox), 1)
        
        # Check email content
        email = mail.outbox[0]
        self.assertEqual(email.subject, f"Your Factory InfoHub Order #{order.order_number}")
        self.assertEqual(email.to, [self.user.email])
        self.assertIn('Order Receipt', email.body)
        self.assertIn(self.factory.name, email.body)
        
        # Check order status was updated
        order.refresh_from_db()
        self.assertTrue(order.receipt_sent)
        self.assertEqual(order.email_status, 'sent')
    
    def test_foreign_key_relationships(self):
        """Test that foreign key relationships are properly configured"""
        # Test Order -> PaymentGateway relationship
        order = Order.objects.create(
            user=self.user,
            total_amount=self.factory.price,
            payment_status='pending',
            gateway_used=self.gateway
        )
        
        # Verify foreign key relationship works
        self.assertEqual(order.gateway_used, self.gateway)
        self.assertEqual(order.gateway_used.name, 'stripe')
        
        # Test Order -> OrderItem relationship
        order_item = OrderItem.objects.create(
            order=order,
            factory=self.factory,
            price_at_purchase=self.factory.price
        )
        
        # Verify foreign key relationship works
        self.assertEqual(order_item.order, order)
        self.assertEqual(order_item.factory, self.factory)
        self.assertIn(order_item, order.items.all())
    
    def test_payment_completed_field(self):
        """Test the payment_completed field functionality"""
        order = Order.objects.create(
            user=self.user,
            total_amount=self.factory.price,
            payment_status='pending',
            gateway_used=self.gateway
        )
        
        # Initially should be False
        self.assertFalse(order.payment_completed)
        
        # Mark as completed
        order.payment_status = 'completed'
        order.payment_completed = True
        order.save()
        
        # Verify field was updated
        order.refresh_from_db()
        self.assertTrue(order.payment_completed)
        self.assertEqual(order.payment_status, 'completed')


def run_tests():
    """Run all payment system tests"""
    print("Running Payment System Tests...")
    print("=" * 50)
    
    # Create test suite
    test_runner = get_runner(settings)
    test_runner = test_runner(verbosity=2, interactive=False)
    
    # Run tests
    failures = test_runner.run_tests(['__main__'])
    
    if failures:
        print(f"\n❌ {failures} test(s) failed")
        return False
    else:
        print("\n✅ All tests passed!")
        return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)