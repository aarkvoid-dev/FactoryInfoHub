#!/usr/bin/env python
"""
Script to verify .env loading and email configuration
Run this to check if your environment is set up correctly
"""

import os
import sys

# Add project to path
sys.path.insert(0, '/var/www/factoryhub')

# Check if environment variables are set
print("=" * 60)
print("ENVIRONMENT VARIABLE CHECK")
print("=" * 60)

email_vars = [
    'EMAIL_HOST_USER',
    'EMAIL_HOST_PASSWORD', 
    'EMAIL_HOST',
    'EMAIL_PORT',
    'EMAIL_USE_TLS',
    'DEFAULT_FROM_EMAIL',
    'CONTACT_EMAIL_RECIPIENTS'
]

for var in email_vars:
    value = os.environ.get(var, 'NOT SET')
    # Mask password for security
    if 'PASSWORD' in var and value != 'NOT SET':
        value = value[:4] + '*' * (len(value) - 4)
    print(f"{var}: {value}")

print("\n" + "=" * 60)
print("DJANGO SETTINGS CHECK")
print("=" * 60)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')

import django
django.setup()

from django.conf import settings

print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
print(f"EMAIL_HOST_PASSWORD: {'***' if settings.EMAIL_HOST_PASSWORD else 'EMPTY'}")
print(f"CONTACT_EMAIL_RECIPIENTS: {settings.CONTACT_EMAIL_RECIPIENTS}")

print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)

if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
    print("✓ Email configuration appears VALID")
    print(f"✓ Backend: {settings.EMAIL_BACKEND}")
else:
    print("✗ Email configuration INVALID - using fallback backend")
    print(f"✗ Backend: {settings.EMAIL_BACKEND}")
    print("✗ This means emails will be printed to console, not sent!")