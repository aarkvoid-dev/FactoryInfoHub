#!/usr/bin/env python3
"""
Test script to validate the new admin factory features:
1. Show Deleted Factories button functionality
2. Hard delete and restore buttons in factory edit form

This script tests the URL patterns and template rendering.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from Karkahan.models import Factory, Category, SubCategory, Country, State, City

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

def test_admin_factory_features():
    """Test the new admin factory features"""
    
    print("🧪 Testing Admin Factory Features")
    print("=" * 50)
    
    # Create test client
    client = Client()
    
    # Create test user with admin privileges
    try:
        admin_user = User.objects.create_superuser(
            username='testadmin',
            email='admin@test.com',
            password='testpass123'
        )
        print("✅ Created test admin user")
    except:
        admin_user = User.objects.get(username='testadmin')
        print("✅ Found existing test admin user")
    
    # Login as admin
    client.login(username='testadmin', password='testpass123')
    print("✅ Logged in as admin")
    
    # Test 1: Check if the factories list page loads
    try:
        response = client.get(reverse('admin_interface:admin_factories'))
        if response.status_code == 200:
            print("✅ Admin factories list page loads successfully")
            
            # Check if the "Show Deleted" button is present in the template
            content = response.content.decode('utf-8')
            if 'toggleDeletedView()' in content:
                print("✅ Show Deleted button JavaScript function found")
            else:
                print("❌ Show Deleted button JavaScript function not found")
                
            if 'Show Deleted' in content or 'Show Active' in content:
                print("✅ Show Deleted/Active button text found")
            else:
                print("❌ Show Deleted/Active button text not found")
                
        else:
            print(f"❌ Admin factories list page failed to load (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Error testing factories list page: {e}")
    
    # Test 2: Check if the factory edit page loads
    try:
        # Create test data first
        category = Category.objects.get_or_create(name='Test Category')[0]
        country = Country.objects.get_or_create(name='Test Country')[0]
        state = State.objects.get_or_create(name='Test State', country=country)[0]
        city = City.objects.get_or_create(name='Test City', state=state)[0]
        
        # Create a test factory
        factory = Factory.objects.create(
            name='Test Factory',
            slug='test-factory',
            category=category,
            country=country,
            state=state,
            city=city,
            created_by=admin_user
        )
        print("✅ Created test factory")
        
        # Test normal factory edit page
        response = client.get(reverse('admin_interface:admin_factory_edit', args=[factory.id]))
        if response.status_code == 200:
            print("✅ Admin factory edit page loads successfully")
            
            # Check if the form is present
            content = response.content.decode('utf-8')
            if 'factoryForm' in content:
                print("✅ Factory form found")
            else:
                print("❌ Factory form not found")
                
        else:
            print(f"❌ Admin factory edit page failed to load (status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Error testing factory edit page: {e}")
    
    # Test 3: Test soft delete functionality
    try:
        # Soft delete the factory
        factory.soft_delete()
        print("✅ Factory soft deleted")
        
        # Test factory edit page for deleted factory
        response = client.get(reverse('admin_interface:admin_factory_edit', args=[factory.id]))
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check if factory actions section is present
            if 'Factory Actions' in content:
                print("✅ Factory Actions section found for deleted factory")
            else:
                print("❌ Factory Actions section not found for deleted factory")
                
            # Check if restore button is present
            if 'Restore Factory' in content:
                print("✅ Restore Factory button found")
            else:
                print("❌ Restore Factory button not found")
                
            # Check if hard delete button is present (for superuser)
            if 'Permanently Delete' in content:
                print("✅ Permanently Delete button found")
            else:
                print("❌ Permanently Delete button not found")
                
            # Check if modal is present
            if 'hardDeleteModal' in content:
                print("✅ Hard delete modal found")
            else:
                print("❌ Hard delete modal not found")
                
        else:
            print(f"❌ Deleted factory edit page failed to load (status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Error testing deleted factory edit page: {e}")
    
    # Test 4: Test URL patterns
    try:
        # Test restore URL
        restore_url = reverse('admin_interface:admin_factory_restore', args=[factory.id])
        print(f"✅ Restore URL generated: {restore_url}")
        
        # Test hard delete URL (from Karkahan app)
        hard_delete_url = reverse('karkahan:factory_hard_delete', args=[factory.slug])
        print(f"✅ Hard delete URL generated: {hard_delete_url}")
        
    except Exception as e:
        print(f"❌ Error testing URL patterns: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Test completed!")
    print("\n📋 Summary:")
    print("- Show Deleted Factories button added to admin factories list")
    print("- Factory Actions section added to edit form for deleted factories")
    print("- Restore and Hard Delete buttons with proper permissions")
    print("- Confirmation modal for hard delete action")
    print("- JavaScript toggle functionality for showing/hiding deleted factories")

if __name__ == '__main__':
    test_admin_factory_features()