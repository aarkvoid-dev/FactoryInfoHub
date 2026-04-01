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
    ) -> bool:
        """
        Send factory details email with comprehensive format for multiple factories
        
        Args:
            user_email: Recipient email address
            user_name: Recipient name
            factories_data: List of factory data dictionaries
        
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Generate email subject
            if len(factories_data) > 1:
                subject = f"Factory Information Package - {len(factories_data)} Factory(ies)"
            else:
                factory_name = factories_data[0]['name']
                subject = f"Factory Information: {factory_name}"
            
            # Create context for template
            context = {
                'user_name': user_name,
                'user_email': user_email,
                'factories': factories_data,
                'email_sent_at': timezone.now(),
                'total_factories': len(factories_data),
            }
            
            # Render HTML content using comprehensive template
            html_content = render_to_string('karkahan/email/comprehensive_factory_details.html', context)
            
            # Create plain text version
            text_content = FactoryEmailService._create_text_content(user_name, factories_data)
            
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
    def _create_text_content(user_name: str, factories_data: List[dict]) -> str:
        """Create plain text version of factory details email"""
        content = f"Factory Details - {user_name}\n\n"
        
        if len(factories_data) > 1:
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
