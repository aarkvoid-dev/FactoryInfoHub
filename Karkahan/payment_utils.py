"""
Payment utilities for Factory InfoHub payment system.

This module contains utility functions for payment processing,
validation, and integration with payment gateways.
"""

import logging
import uuid
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from .email_service import FactoryEmailService

from .models import FactoryPurchase, Order, Payment, PurchaseHistory, Factory
from .models import ShoppingCart, OrderItem

logger = logging.getLogger(__name__)


class PaymentProcessor:
    """Handles payment processing and validation"""
    
    @staticmethod
    def validate_payment_amount(amount):
        """Validate payment amount"""
        try:
            amount = Decimal(str(amount))
            if amount <= 0:
                raise ValidationError("Payment amount must be greater than zero")
            if amount > 999999999:
                raise ValidationError("Payment amount is too large")
            return amount
        except (ValueError, TypeError, Decimal.InvalidOperation):
            raise ValidationError("Invalid payment amount format")

    @staticmethod
    def generate_transaction_reference():
        """Generate unique transaction reference"""
        return f"TXN-{timezone.now().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"

    @staticmethod
    def calculate_order_totals(order):
        """Calculate order totals including tax and fees"""
        subtotal = sum(item.total_price for item in order.items.all())
        tax_rate = Decimal('0.18')  # 18% GST
        tax_amount = subtotal * tax_rate
        service_fee = Decimal('0.0')  # No service fee for now
        total_amount = subtotal + tax_amount + service_fee
        
        order.subtotal = subtotal
        order.tax_amount = tax_amount
        order.service_fee = service_fee
        order.total_amount = total_amount
        order.save()
        
        return total_amount

    @staticmethod
    def create_payment_record(order, payment_method, amount):
        """Create a payment record for an order"""
        payment = Payment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=amount,
            currency='INR',
            transaction_id=PaymentProcessor.generate_transaction_reference(),
            status='pending'
        )
        return payment

    @staticmethod
    def process_order_payment(order, payment_method):
        """Process payment for an order"""
        try:
            # Calculate totals
            total_amount = PaymentProcessor.calculate_order_totals(order)
            
            # Create payment record
            payment = PaymentProcessor.create_payment_record(
                order=order,
                payment_method=payment_method,
                amount=total_amount
            )
            
            # Mark order as processing
            order.payment_status = 'processing'
            order.status = 'processing'
            order.save()
            
            logger.info(f"Payment initiated for order {order.order_number}, amount: {total_amount}")
            
            return payment, total_amount
            
        except Exception as e:
            logger.error(f"Error processing order payment: {str(e)}")
            raise ValidationError(f"Failed to process payment: {str(e)}")

    @staticmethod
    def complete_order_payment(order, payment_method, gateway_response=None):
        """Complete an order payment"""
        try:
            # Get or create payment record
            payment = order.payments.first()
            if not payment:
                payment = PaymentProcessor.create_payment_record(
                    order=order,
                    payment_method=payment_method,
                    amount=order.total_amount
                )
            
            # Mark payment as completed
            payment.mark_as_completed(gateway_response)
            
            # Mark order as completed
            order.mark_as_completed()
            
            # Clear shopping cart
            ShoppingCart.objects.filter(user=order.user).delete()
            
            # Send confirmation email
            PaymentProcessor.send_order_confirmation_email(order)
            
            # Create FactoryPurchase records and send factory details emails
            PaymentProcessor.create_factory_purchases_and_send_emails(order)
            
            logger.info(f"Order {order.order_number} payment completed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error completing order payment: {str(e)}")
            raise ValidationError(f"Failed to complete payment: {str(e)}")

    @staticmethod
    def create_factory_purchases_and_send_emails(order):
        """Create FactoryPurchase records and send factory details emails for order items"""
        try:
            for order_item in order.items.all():
                factory = order_item.factory
                user = order.user
                
                # Check if user already purchased this factory
                if not factory.has_user_purchased(user):
                    # Create FactoryPurchase record
                    purchase = FactoryPurchase.objects.create(
                        user=user,
                        factory=factory,
                        quantity=order_item.quantity,
                        price_at_purchase=order_item.price_at_purchase,
                        payment_status='completed',
                        transaction_id=order.order_number
                    )
                    
                    # Send factory details email
                    purchase.send_factory_details_email()
                    
                    # Create PurchaseHistory record
                    PurchaseHistory.create_from_purchase(purchase)
                    
                    logger.info(f"Created FactoryPurchase and sent email for factory {factory.name} to user {user.username}")
                else:
                    logger.info(f"User {user.username} already purchased factory {factory.name}, skipping email")
            
        except Exception as e:
            logger.error(f"Error creating factory purchases or sending emails: {str(e)}")
            # Don't raise exception as this shouldn't block order completion

    @staticmethod
    def process_legacy_purchase(factory, user, quantity=1):
        """Process legacy factory purchase"""
        try:
            # Check if already purchased
            if factory.has_user_purchased(user):
                raise ValidationError("You have already purchased this factory")
            
            # Create purchase record
            purchase = FactoryPurchase.objects.create(
                user=user,
                factory=factory,
                quantity=quantity,
                price_at_purchase=factory.price,
                payment_status='pending'
            )
            
            logger.info(f"Legacy purchase created for user {user.username}, factory {factory.name}")
            
            return purchase
            
        except Exception as e:
            logger.error(f"Error processing legacy purchase: {str(e)}")
            raise ValidationError(f"Failed to process purchase: {str(e)}")

    @staticmethod
    def complete_legacy_purchase(purchase):
        """Complete a legacy factory purchase"""
        try:
            # Mark purchase as completed
            purchase.mark_as_completed()
            
            # Create purchase history record
            PurchaseHistory.create_from_purchase(purchase)
            
            logger.info(f"Legacy purchase {purchase.id} completed for user {purchase.user.username}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error completing legacy purchase: {str(e)}")
            raise ValidationError(f"Failed to complete purchase: {str(e)}")

    @staticmethod
    def send_order_confirmation_email(order):
        """Send order confirmation email using centralized email service"""
        return FactoryEmailService.send_order_confirmation_email(order)

    @staticmethod
    def send_factory_details_email(purchase):
        """Send factory details email for legacy purchases"""
        try:
            subject = f"Factory Details: {purchase.factory.name}"
            
            # Create HTML email content
            html_content = render_to_string('karkahan/email/factory_details.html', {
                'purchase': purchase,
                'factory': purchase.factory,
                'user': purchase.user,
            })
            
            # Create plain text version
            text_content = f"""
            Factory Details: {purchase.factory.name}
            
            Dear {purchase.user.username},
            
            Thank you for your purchase! Here are the details for the factory you requested:
            
            Factory Name: {purchase.factory.name}
            Category: {purchase.factory.category.name}
            Location: {purchase.factory.full_address}
            Type: {purchase.factory.factory_type}
            Production Capacity: {purchase.factory.production_capacity}
            Employee Count: {purchase.factory.employee_count}
            Established: {purchase.factory.established_year}
            Annual Turnover: {purchase.factory.annual_turnover}
            
            Contact Information:
            Contact Person: {purchase.factory.contact_person}
            Phone: {purchase.factory.contact_phone}
            Email: {purchase.factory.contact_email}
            Website: {purchase.factory.website}
            
            Address: {purchase.factory.address}
            {purchase.factory.city.name}, {purchase.factory.state.name} - {purchase.factory.pincode}
            {purchase.factory.country.name}
            
            This information is confidential and intended solely for your use.
            
            Best regards,
            Factory InfoHub Team
            """
            
            # Send email
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[purchase.user.email],
                html_message=html_content,
                fail_silently=False,
            )
            
            # Update purchase record
            purchase.email_sent = True
            purchase.email_sent_at = timezone.now()
            purchase.save()
            
            logger.info(f"Factory details email sent to {purchase.user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send factory details email: {str(e)}")
            # Don't raise exception as this shouldn't block the purchase completion

    @staticmethod
    def validate_order_items(order):
        """Validate order items before processing"""
        if not order.items.exists():
            raise ValidationError("Order contains no items")
        
        for item in order.items.all():
            if item.quantity < 1:
                raise ValidationError(f"Invalid quantity for {item.factory.name}")
            
            if item.price_at_purchase <= 0:
                raise ValidationError(f"Invalid price for {item.factory.name}")
            
            # Check if factory is still active
            if not item.factory.is_active or item.factory.is_deleted:
                raise ValidationError(f"Factory {item.factory.name} is no longer available")

    @staticmethod
    def calculate_refund_amount(payment, requested_amount=None):
        """Calculate refund amount"""
        max_refundable = payment.amount - payment.refunded_amount
        
        if requested_amount is None:
            return max_refundable
        
        requested_amount = Decimal(str(requested_amount))
        
        if requested_amount <= 0:
            raise ValidationError("Refund amount must be greater than zero")
        
        if requested_amount > max_refundable:
            raise ValidationError(f"Refund amount exceeds available balance. Max refundable: {max_refundable}")
        
        return requested_amount

    @staticmethod
    def process_refund(payment, amount=None, reason=""):
        """Process payment refund"""
        try:
            refund_amount = PaymentProcessor.calculate_refund_amount(payment, amount)
            
            # Process refund (in real implementation, this would call payment gateway)
            payment.process_refund(refund_amount, reason)
            
            # Update order status if fully refunded
            order = payment.order
            total_paid = sum(p.amount for p in order.payments.all() if p.status == 'completed')
            total_refunded = sum(p.refunded_amount for p in order.payments.all())
            
            if total_refunded >= total_paid:
                order.status = 'refunded'
                order.payment_status = 'refunded'
                order.save()
            
            logger.info(f"Refund processed for payment {payment.transaction_id}, amount: {refund_amount}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing refund: {str(e)}")
            raise ValidationError(f"Failed to process refund: {str(e)}")


def get_payment_methods():
    """Get available payment methods"""
    return [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
        ('cod', 'Cash on Delivery'),
    ]


def get_payment_status_choices():
    """Get payment status choices"""
    return [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
        ('chargeback', 'Chargeback'),
    ]


def format_currency(amount):
    """Format amount as currency"""
    try:
        amount = Decimal(str(amount))
        return f"Rs. {amount:,.2f}"
    except (ValueError, TypeError, Decimal.InvalidOperation):
        return "Rs. 0.00"


PaymentProcessor.format_currency = staticmethod(format_currency)


def get_order_status_display(status):
    """Get human-readable order status"""
    status_map = {
        'pending': 'Pending',
        'processing': 'Processing',
        'completed': 'Completed',
        'cancelled': 'Cancelled',
        'refunded': 'Refunded',
    }
    return status_map.get(status, status.title())