#!/usr/bin/env python3
"""
Mock Razorpay implementation for testing and development
This provides a fallback when the actual Razorpay package cannot be installed
"""

import json
import logging
from decimal import Decimal
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

class MockRazorpayClient:
    """Mock Razorpay client for testing and development"""
    
    def __init__(self, auth=None):
        self.auth = auth
        self.orders = {}
        self.payments = {}
        self.refunds = {}
        
    def order_create(self, data):
        """Mock order creation"""
        order_id = f"mock_order_{timezone.now().strftime('%Y%m%d_%H%M%S')}_{id(data)}"
        
        order_data = {
            'id': order_id,
            'amount': data.get('amount', 0),
            'currency': data.get('currency', 'INR'),
            'receipt': data.get('receipt', ''),
            'status': 'created',
            'created_at': int(timezone.now().timestamp()),
            'notes': data.get('notes', {}),
        }
        
        self.orders[order_id] = order_data
        logger.info(f"Mock order created: {order_id}")
        
        return order_data
    
    def payment_fetch(self, payment_id):
        """Mock payment fetch"""
        payment_data = {
            'id': payment_id,
            'amount': 10000,  # 100.00 INR in paise
            'currency': 'INR',
            'status': 'captured',
            'order_id': 'mock_order_123',
            'description': 'Test payment',
            'created_at': int(timezone.now().timestamp()),
        }
        
        return payment_data
    
    def payment_capture(self, payment_id, capture_data):
        """Mock payment capture"""
        return {
            'id': payment_id,
            'captured': True,
            'amount': capture_data.get('amount', 10000),
            'currency': capture_data.get('currency', 'INR'),
        }
    
    def payment_refund(self, payment_id, refund_data):
        """Mock payment refund"""
        refund_id = f"mock_refund_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
        
        refund_amount = refund_data.get('amount', 10000)
        
        refund_data = {
            'id': refund_id,
            'payment_id': payment_id,
            'amount': refund_amount,
            'currency': 'INR',
            'status': 'processed',
            'created_at': int(timezone.now().timestamp()),
        }
        
        self.refunds[refund_id] = refund_data
        logger.info(f"Mock refund created: {refund_id}")
        
        return refund_data
    
    def order_fetch(self, order_id):
        """Mock order fetch"""
        return self.orders.get(order_id, {
            'id': order_id,
            'status': 'not_found',
        })
    
    def utility_verify_payment_signature(self, params_dict):
        """Mock signature verification"""
        # For testing, we'll accept any signature
        logger.info("Mock signature verification called")
        return True

def get_razorpay_client():
    """Get Razorpay client instance with fallback to mock"""
    try:
        import razorpay
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    except ImportError:
        logger.warning("Razorpay package not available, using mock client")
        return MockRazorpayClient(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    except Exception as e:
        logger.error(f"Error initializing Razorpay client: {e}")
        return MockRazorpayClient()

# Mock utility functions
def create_razorpay_order(amount, currency='INR', receipt=None, notes=None):
    """Create a Razorpay order (mock)"""
    try:
        client = get_razorpay_client()
        order_data = {
            'amount': int(amount * 100),  # Convert to paise
            'currency': currency,
            'receipt': receipt or f'order_{timezone.now().strftime("%Y%m%d_%H%M%S")}',
            'payment_capture': 1,
            'notes': notes or {}
        }
        
        if hasattr(client, 'order_create'):
            # Mock client
            return client.order_create(order_data)
        else:
            # Real Razorpay client
            return client.order.create(data=order_data)
            
    except Exception as e:
        logger.error(f"Error creating Razorpay order: {str(e)}")
        raise Exception(f"Failed to create payment order: {str(e)}")

def verify_payment_signature(params_dict):
    """Verify Razorpay payment signature (mock)"""
    try:
        client = get_razorpay_client()
        
        if hasattr(client, 'utility_verify_payment_signature'):
            # Mock client
            return client.utility_verify_payment_signature(params_dict)
        else:
            # Real Razorpay client
            client.utility.verify_payment_signature(params_dict)
            return True
            
    except Exception as e:
        logger.error(f"Payment signature verification failed: {str(e)}")
        return False

def get_payment_details(payment_id):
    """Get payment details from Razorpay (mock)"""
    try:
        client = get_razorpay_client()
        
        if hasattr(client, 'payment_fetch'):
            # Mock client
            return client.payment_fetch(payment_id)
        else:
            # Real Razorpay client
            return client.payment.fetch(payment_id)
            
    except Exception as e:
        logger.error(f"Error fetching payment details: {str(e)}")
        return None

def capture_payment(payment_id, amount):
    """Capture a payment (mock)"""
    try:
        client = get_razorpay_client()
        
        capture_data = {
            'amount': int(amount * 100),
            'currency': 'INR'
        }
        
        if hasattr(client, 'payment_capture'):
            # Mock client
            return client.payment_capture(payment_id, capture_data)
        else:
            # Real Razorpay client
            return client.payment.capture(payment_id, capture_data)
            
    except Exception as e:
        logger.error(f"Error capturing payment: {str(e)}")
        return None

def refund_payment(payment_id, amount=None):
    """Refund a payment (mock)"""
    try:
        client = get_razorpay_client()
        
        refund_data = {}
        if amount:
            refund_data['amount'] = int(amount * 100)
        
        if hasattr(client, 'payment_refund'):
            # Mock client
            return client.payment_refund(payment_id, refund_data)
        else:
            # Real Razorpay client
            return client.payment.refund(payment_id, refund_data)
            
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        return None

def get_order_details(order_id):
    """Get order details from Razorpay (mock)"""
    try:
        client = get_razorpay_client()
        
        if hasattr(client, 'order_fetch'):
            # Mock client
            return client.order_fetch(order_id)
        else:
            # Real Razorpay client
            return client.order.fetch(order_id)
            
    except Exception as e:
        logger.error(f"Error fetching order details: {str(e)}")
        return None

def process_payment_completion(order, payment_id, signature):
    """Process payment completion and update order status (mock)"""
    try:
        # Verify payment signature
        params_dict = {
            'razorpay_order_id': order.id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }
        
        if not verify_payment_signature(params_dict):
            raise Exception("Payment signature verification failed")
        
        # Get payment details
        payment_details = get_payment_details(payment_id)
        if not payment_details:
            raise Exception("Could not fetch payment details")
        
        # Verify payment amount
        expected_amount = order.total_amount
        actual_amount = Decimal(payment_details['amount']) / 100
        
        if actual_amount != expected_amount:
            raise Exception(f"Payment amount mismatch: expected {expected_amount}, got {actual_amount}")
        
        # Update order and payment records
        order.status = 'completed'
        order.payment_status = 'completed'
        order.completed_at = timezone.now()
        order.save()
        
        # Update payment record
        payment = order.payments.first()
        if payment:
            payment.status = 'completed'
            payment.transaction_id = payment_id
            payment.gateway_response = payment_details
            payment.completed_at = timezone.now()
            payment.save()
        
        # Create factory purchases for each order item
        from .models import FactoryPurchase
        
        for item in order.items.all():
            FactoryPurchase.objects.create(
                user=order.user,
                factory=item.factory,
                quantity=item.quantity,
                price_at_purchase=item.price_at_purchase,
                payment_status='completed',
                transaction_id=payment_id
            )
        
        # Clear user's cart
        from .models import ShoppingCart
        ShoppingCart.objects.filter(user=order.user).delete()
        
        return True, "Payment completed successfully"
        
    except Exception as e:
        logger.error(f"Payment completion failed: {str(e)}")
        # Mark order as failed
        if order:
            order.status = 'failed'
            order.payment_status = 'failed'
            order.save()
            if order.payments.first():
                order.payments.first().status = 'failed'
                order.payments.first().gateway_error = str(e)
                order.payments.first().save()
        return False, str(e)

def create_payment_options():
    """Create payment options for Razorpay checkout"""
    return {
        'key': settings.RAZORPAY_KEY_ID,
        'amount': 0,  # Will be set dynamically
        'currency': 'INR',
        'name': 'Factory InfoHub',
        'description': 'Factory Information Purchase',
        'image': '/static/images/logo.png',  # Add your logo path
        'order_id': '',  # Will be set dynamically
        'callback_url': '/karkahan/payment/success/',
        'prefill': {
            'name': '',
            'email': '',
            'contact': ''
        },
        'notes': {
            'purpose': 'Factory Information Purchase'
        },
        'theme': {
            'color': '#EB662B'
        }
    }