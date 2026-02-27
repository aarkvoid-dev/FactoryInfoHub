"""
Factory InfoHub Email Service

Centralized email service for sending factory information emails.
Handles both single and multiple factory emails in a consistent, maintainable way.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from decimal import Decimal
from typing import List, Union


logger = logging.getLogger(__name__)


class FactoryEmailService:
    """Centralized email service for factory information emails"""
    
    @staticmethod
    def send_factory_details_email(
        user_email: str, 
        user_name: str, 
        factories_data: List[dict],
        order_number: str = None,
        is_bulk: bool = False
    ) -> bool:
        """
        Send factory details email with table format for multiple factories
        
        Args:
            user_email: Recipient email address
            user_name: Recipient name
            factories_data: List of factory data dictionaries
            order_number: Order number (if from order)
            is_bulk: Whether this is a bulk email (multiple factories)
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Generate email subject
            if is_bulk:
                subject = f"Factory Details - {len(factories_data)} Factory(ies) - Order {order_number}" if order_number else f"Factory Details - {len(factories_data)} Factory(ies)"
            else:
                factory_name = factories_data[0]['name']
                subject = f"Factory Details: {factory_name}"
            
            # Create context for template
            context = {
                'user_name': user_name,
                'factories': factories_data,
                'order_number': order_number,
                'is_bulk': is_bulk,
                'email_sent_at': timezone.now(),
                'total_factories': len(factories_data),
            }
            
            # Render HTML content
            html_content = render_to_string('karkahan/email/factory_details.html', context)
            
            # Create plain text version
            text_content = FactoryEmailService._create_text_content(user_name, factories_data, order_number, is_bulk)
            
            # Create and send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            # Log success
            logger.info(f"Factory details email sent to {user_email} for {len(factories_data)} factory(ies)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send factory details email to {user_email}: {str(e)}")
            return False

    @staticmethod
    def _create_text_content(user_name: str, factories_data: List[dict], order_number: str = None, is_bulk: bool = False) -> str:
        """Create plain text version of factory details email"""
        content = f"Factory Details - {user_name}\n\n"
        
        if order_number:
            content += f"Order Number: {order_number}\n\n"
        
        if is_bulk:
            content += f"Total Factories: {len(factories_data)}\n\n"
        
        for i, factory in enumerate(factories_data, 1):
            content += f"--- Factory {i}: {factory['name']} ---\n"
            content += f"Category: {factory['category']}\n"
            content += f"Location: {factory['location']}\n"
            content += f"Type: {factory.get('factory_type', 'Not specified')}\n"
            content += f"Production Capacity: {factory.get('production_capacity', 'Not specified')}\n"
            content += f"Employee Count: {factory.get('employee_count', 'Not specified')}\n"
            content += f"Established: {factory.get('established_year', 'Not specified')}\n"
            content += f"Annual Turnover: {factory.get('annual_turnover', 'Not specified')}\n\n"
            
            content += "Contact Information:\n"
            content += f"Contact Person: {factory.get('contact_person', 'Not specified')}\n"
            content += f"Phone: {factory.get('contact_phone', 'Not specified')}\n"
            content += f"Email: {factory.get('contact_email', 'Not specified')}\n"
            content += f"Website: {factory.get('website', 'Not specified')}\n\n"
            
            content += "Address:\n"
            content += f"{factory.get('address', '')}\n"
            content += f"{factory.get('city', '')}, {factory.get('state', '')} - {factory.get('pincode', '')}\n"
            content += f"{factory.get('country', '')}\n\n"
        
        content += "This information is confidential and intended solely for your use.\n\n"
        content += "Best regards,\nFactory InfoHub Team"
        
        return content

    @staticmethod
    def send_order_confirmation_email(order) -> bool:
        """Send order confirmation email"""
        try:
            # Import models inside the function to avoid circular imports
            from .models import Order
            
            subject = f"Order Confirmation - {order.order_number}"
            
            # Create context for template
            context = {
                'order': order,
                'user_name': order.customer_name,
                'items': order.items.all(),
            }
            
            # Render HTML content
            html_content = render_to_string('karkahan/email/order_confirmation.html', context)
            
            # Create plain text version
            text_content = FactoryEmailService._create_order_text_content(order)
            
            # Create and send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[order.customer_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()
            
            logger.info(f"Order confirmation email sent to {order.customer_email} for order {order.order_number}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email for order {order.order_number}: {str(e)}")
            return False

    @staticmethod
    def _create_order_text_content(order) -> str:
        """Create plain text version of order confirmation email"""
        content = f"Order Confirmation - {order.order_number}\n\n"
        content += f"Dear {order.customer_name},\n\n"
        content += "Thank you for your order! We're pleased to confirm your purchase.\n\n"
        
        content += "Order Details:\n"
        content += f"Order Number: {order.order_number}\n"
        content += f"Date: {order.created_at.strftime('%B %d, %Y')}\n\n"
        
        content += "Items:\n"
        for item in order.items.all():
            content += f"- {item.factory.name} x{item.quantity}\n"
            content += f"  Price: Rs. {item.price_at_purchase}\n"
            content += f"  Total: Rs. {item.total_price}\n\n"
        
        content += f"Subtotal: Rs. {order.subtotal}\n"
        content += f"Tax (18%): Rs. {order.tax_amount}\n"
        content += f"Service Fee: Rs. {order.service_fee}\n"
        content += f"Total Amount: Rs. {order.total_amount}\n\n"
        
        content += f"Payment Status: {order.payment_status.title()}\n"
        content += f"Order Status: {order.status.title()}\n\n"
        content += "Factory details will be sent to your email shortly.\n\n"
        content += "Best regards,\nFactory InfoHub Team"
        
        return content

    @staticmethod
    def send_bulk_factory_emails(user_email: str, user_name: str, order) -> bool:
        """Send bulk factory details email for an order with multiple factories"""
        try:
            # Import models inside the function to avoid circular imports
            from .models import Order, FactoryPurchase, PurchaseHistory
            
            # Get factory data for all items in the order
            factories_data = []
            for item in order.items.all():
                factory = item.factory
                factory_data = {
                    'name': factory.name,
                    'category': factory.category.name,
                    'location': factory.full_address,
                    'factory_type': factory.factory_type or 'Not specified',
                    'production_capacity': factory.production_capacity or 'Not specified',
                    'employee_count': factory.employee_count or 'Not specified',
                    'established_year': factory.established_year or 'Not specified',
                    'annual_turnover': factory.annual_turnover or 'Not specified',
                    'contact_person': factory.contact_person or 'Not specified',
                    'contact_phone': factory.contact_phone or 'Not specified',
                    'contact_email': factory.contact_email or 'Not specified',
                    'website': factory.website or 'Not specified',
                    'address': factory.address or '',
                    'city': factory.city.name if factory.city else '',
                    'state': factory.state.name if factory.state else '',
                    'pincode': factory.pincode or '',
                    'country': factory.country.name if factory.country else '',
                }
                factories_data.append(factory_data)
            
            # Send bulk email
            success = FactoryEmailService.send_factory_details_email(
                user_email=user_email,
                user_name=user_name,
                factories_data=factories_data,
                order_number=order.order_number,
                is_bulk=True
            )
            
            if success:
                # Update FactoryPurchase records as sent
                FactoryEmailService._mark_purchases_as_sent(order)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to send bulk factory emails for order {order.order_number}: {str(e)}")
            return False

    @staticmethod
    def _mark_purchases_as_sent(order):
        """Mark all FactoryPurchase records for an order as sent"""
        try:
            from .models import Order, FactoryPurchase, PurchaseHistory
            current_time = timezone.now()
            for item in order.items.all():
                # Find the corresponding FactoryPurchase
                purchase = FactoryPurchase.objects.filter(
                    user=order.user,
                    factory=item.factory,
                    payment_status='completed'
                ).first()
                
                if purchase:
                    purchase.email_sent = True
                    purchase.email_sent_at = current_time
                    purchase.save()
                    
                    # Update corresponding PurchaseHistory record
                    try:
                        purchase_history = PurchaseHistory.objects.filter(
                            user=purchase.user,
                            factory_slug=purchase.factory.slug,
                            purchase_date=purchase.purchased_at
                        ).first()
                        
                        if purchase_history:
                            purchase_history.email_delivered = True
                            purchase_history.email_delivered_at = current_time
                            purchase_history.save()
                    except Exception as history_error:
                        logger.warning(f"Could not update PurchaseHistory record: {history_error}")
            
            logger.info(f"Marked FactoryPurchase records as sent for order {order.order_number}")
            
        except Exception as e:
            logger.error(f"Failed to mark purchases as sent for order {order.order_number}: {str(e)}")

    @staticmethod
    def send_single_factory_email(user_email: str, user_name: str, factory) -> bool:
        """Send email for a single factory purchase"""
        try:
            # Import models inside the function to avoid circular imports
            from .models import Factory
            
            factory_data = [{
                'name': factory.name,
                'category': factory.category.name,
                'location': factory.full_address,
                'factory_type': factory.factory_type or 'Not specified',
                'production_capacity': factory.production_capacity or 'Not specified',
                'employee_count': factory.employee_count or 'Not specified',
                'established_year': factory.established_year or 'Not specified',
                'annual_turnover': factory.annual_turnover or 'Not specified',
                'contact_person': factory.contact_person or 'Not specified',
                'contact_phone': factory.contact_phone or 'Not specified',
                'contact_email': factory.contact_email or 'Not specified',
                'website': factory.website or 'Not specified',
                'address': factory.address or '',
                'city': factory.city.name if factory.city else '',
                'state': factory.state.name if factory.state else '',
                'pincode': factory.pincode or '',
                'country': factory.country.name if factory.country else '',
            }]
            
            return FactoryEmailService.send_factory_details_email(
                user_email=user_email,
                user_name=user_name,
                factories_data=factory_data,
                is_bulk=False
            )
            
        except Exception as e:
            logger.error(f"Failed to send single factory email to {user_email}: {str(e)}")
            return False