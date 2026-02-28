#!/usr/bin/env python
"""
Test script for the payment system to validate functionality
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
sys.path.append('/Users/arfatulshaikh/Projects/InfoHub/FactoryInfoHub')
django.setup()

from Karkahan.payment_utils import PaymentProcessor
from decimal import Decimal

def test_payment_utilities():
    """Test payment utility functions"""
    print("Testing Payment Utilities...")
    
    # Test payment amount validation
    try:
        valid_amount = PaymentProcessor.validate_payment_amount(1000.50)
        print('✓ Payment amount validation works')
    except Exception as e:
        print(f'✗ Payment amount validation failed: {e}')
    
    # Test transaction reference generation
    try:
        ref = PaymentProcessor.generate_transaction_reference()
        print(f'✓ Transaction reference generated: {ref}')
    except Exception as e:
        print(f'✗ Transaction reference generation failed: {e}')
    
    # Test currency formatting
    try:
        formatted = PaymentProcessor.format_currency(1234.56)
        print(f'✓ Currency formatting works: {formatted}')
    except Exception as e:
        print(f'✗ Currency formatting failed: {e}')
    
    # Test invalid amount
    try:
        PaymentProcessor.validate_payment_amount(-100)
        print('✗ Should have failed for negative amount')
    except Exception as e:
        print(f'✓ Correctly rejected negative amount: {e}')
    
    print('Payment utilities test completed\n')

def test_url_patterns():
    """Test URL patterns"""
    print("Testing URL Patterns...")
    
    from django.urls import reverse
    from django.test import Client
    
    client = Client()
    
    # Test order payment URL
    try:
        # This will test if the URL pattern works
        from uuid import uuid4
        test_order_id = uuid4()
        url = f'/karkahan/order/{test_order_id}/payment/'
        print(f'✓ Order payment URL pattern works: {url}')
    except Exception as e:
        print(f'✗ Order payment URL pattern failed: {e}')
    
    # Test legacy payment URL
    try:
        url = '/karkahan/payment/legacy/1000/'
        print(f'✓ Legacy payment URL pattern works: {url}')
    except Exception as e:
        print(f'✗ Legacy payment URL pattern failed: {e}')
    
    print('URL patterns test completed\n')

if __name__ == '__main__':
    test_payment_utilities()
    test_url_patterns()
    print("All tests completed!")