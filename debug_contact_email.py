#!/usr/bin/env python3
"""
Debug script to test contact form email functionality
"""

import os
import sys
import django
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, '/Users/arfatulshaikh/Projects/InfoHub/FactoryInfoHub')

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

from django.core.mail import send_mail
from django.test import RequestFactory
from django.contrib.auth.models import User
from Home.views import contact
from Home.models import ContactMessage


def test_email_configuration():
    """Test email configuration and sending"""
    print("=== EMAIL CONFIGURATION TEST ===")
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'EMPTY'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"CONTACT_EMAIL_RECIPIENTS: {getattr(settings, 'CONTACT_EMAIL_RECIPIENTS', [])}")
    print()

def test_simple_email():
    """Test sending a simple email"""
    print("=== SIMPLE EMAIL TEST ===")
    try:
        result = send_mail(
            'Test Subject',
            'This is a test email from the debug script.',
            settings.DEFAULT_FROM_EMAIL,
            ['test@example.com'],
            fail_silently=False,
        )
        print(f"✅ Simple email test result: {result}")
    except Exception as e:
        print(f"❌ Simple email test failed: {e}")
    print()

def test_contact_form_email():
    """Test the actual contact form email sending logic"""
    print("=== CONTACT FORM EMAIL TEST ===")
    
    # Create a test user
    try:
        user = User.objects.get(username='testuser')
    except User.DoesNotExist:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    # Create a test contact message
    contact_message = ContactMessage.objects.create(
        name='Test User',
        email='test@example.com',
        subject='Test Contact Form Email',
        message='This is a test message to verify email sending.',
        user=user
    )
    
    print(f"Created test contact message: {contact_message.id}")
    
    # Test admin email
    print("Testing admin email...")
    try:
        admin_subject = f"New Contact Form Submission: {contact_message.subject}"
        admin_message = f"""
New contact form submission received:

Name: {contact_message.name}
Email: {contact_message.email}
Subject: {contact_message.subject}
User: {contact_message.user.username if contact_message.user else 'Anonymous'}
Date: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S %Z')}

Message:
{contact_message.message}

---
This message was sent from FactoryInfoHub contact form.
"""
        
        admin_recipients = getattr(settings, 'CONTACT_EMAIL_RECIPIENTS', [settings.DEFAULT_FROM_EMAIL])
        print(f"Sending to: {admin_recipients}")
        
        result = send_mail(
            admin_subject,
            admin_message,
            settings.DEFAULT_FROM_EMAIL,
            admin_recipients,
            fail_silently=False,
        )
        print(f"✅ Admin email sent successfully: {result}")
        
    except Exception as e:
        print(f"❌ Admin email failed: {e}")
    
    # Test user confirmation email
    print("Testing user confirmation email...")
    try:
        user_subject = "Thank you for your message!"
        user_message = f"""
Dear {contact_message.name},

Thank you for contacting FactoryInfoHub! 

We have received your message and will get back to you within 24 hours.

Your message details:
Subject: {contact_message.subject}
Message: {contact_message.message[:200]}{'...' if len(contact_message.message) > 200 else ''}

Best regards,
FactoryInfoHub Team

---
If you have any urgent inquiries, please contact us at:
Email: support@factoryinfohub.com
Phone: +91 22 1234 5678
"""
        
        result = send_mail(
            user_subject,
            user_message,
            settings.DEFAULT_FROM_EMAIL,
            [contact_message.email],
            fail_silently=True,  # Don't fail if user email is invalid
        )
        print(f"✅ User confirmation email sent: {result}")
        
    except Exception as e:
        print(f"❌ User confirmation email failed: {e}")
    
    print()

def check_database():
    """Check if contact messages are being saved"""
    print("=== DATABASE CHECK ===")
    contact_messages = ContactMessage.objects.all().order_by('-created_at')[:5]
    print(f"Total contact messages in database: {ContactMessage.objects.count()}")
    print("Latest 5 messages:")
    for msg in contact_messages:
        print(f"  - {msg.name} ({msg.email}) - {msg.subject} - {msg.created_at}")
    print()

def main():
    """Run all tests"""
    print("Contact Form Email Debug Script")
    print("=" * 50)
    print()
    
    test_email_configuration()
    test_simple_email()
    test_contact_form_email()
    check_database()
    
    print("=== SUMMARY ===")
    print("If emails are not being sent, check:")
    print("1. EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct")
    print("2. Gmail App Password is being used (not regular password)")
    print("3. 2-Factor Authentication is enabled on Gmail")
    print("4. App Password has been generated correctly")
    print("5. Firewall or network is not blocking SMTP")
    print("6. Try setting EMAIL_BACKEND to 'django.core.mail.backends.console.EmailBackend' to see emails in console")

if __name__ == '__main__':
    main()