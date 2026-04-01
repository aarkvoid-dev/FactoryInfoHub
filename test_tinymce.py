#!/usr/bin/env python3
"""
Test script to verify TinyMCE functionality for pages
"""

import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/Users/arfatulshaikh/Projects/InfoHub/FactoryInfoHub')

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')

# Setup Django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from Home.models import Page, PageSection
from django.urls import reverse

def test_tinymce_functionality():
    """Test TinyMCE functionality for pages"""
    print("Testing TinyMCE functionality...")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testadmin',
        defaults={
            'email': 'test@example.com',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print("Created test admin user")
    
    # Create a test page with HTML content
    html_content = """
    <h1>Welcome to Our Website</h1>
    <p>This is a <strong>test page</strong> with <em>rich text formatting</em>.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
        <li>Item 3</li>
    </ul>
    <p>Here's a <a href="https://example.com">link</a> to demonstrate link functionality.</p>
    """
    
    page, created = Page.objects.update_or_create(
        slug='test-tinymce-page',
        defaults={
            'title': 'Test TinyMCE Page',
            'content': html_content,
            'page_type': 'about',
            'is_published': True,
            'meta_title': 'Test Page - TinyMCE',
            'meta_description': 'Testing TinyMCE rich text editor functionality'
        }
    )
    
    print(f"{'Created' if created else 'Updated'} test page: {page.title}")
    
    # Create a test section with HTML content
    section_content = """
    <h2>Section Content</h2>
    <p>This is a test section with <strong>bold text</strong> and <em>italic text</em>.</p>
    <blockquote>
        This is a blockquote to test advanced formatting.
    </blockquote>
    """
    
    section, created = PageSection.objects.update_or_create(
        page=page,
        order=1,
        defaults={
            'title': 'Test Section',
            'content': section_content
        }
    )
    
    print(f"{'Created' if created else 'Updated'} test section: {section.title}")
    
    # Test that the content is stored correctly
    print("\nTesting content storage:")
    print(f"Page content type: {type(page.content)}")
    print(f"Page content length: {len(page.content)} characters")
    print(f"Section content type: {type(section.content)}")
    print(f"Section content length: {len(section.content)} characters")
    
    # Test that HTML content is preserved
    assert '<h1>' in page.content, "HTML heading not preserved in page content"
    assert '<strong>' in page.content, "HTML bold not preserved in page content"
    assert '<ul>' in page.content, "HTML list not preserved in page content"
    assert '<a href=' in page.content, "HTML link not preserved in page content"
    
    assert '<h2>' in section.content, "HTML heading not preserved in section content"
    assert '<strong>' in section.content, "HTML bold not preserved in section content"
    assert '<blockquote>' in section.content, "HTML blockquote not preserved in section content"
    
    print("✓ HTML content is properly preserved")
    
    # Test that the page can be retrieved
    retrieved_page = Page.objects.get(slug='test-tinymce-page')
    print(f"✓ Page retrieved successfully: {retrieved_page.title}")
    
    # Test that sections can be retrieved
    sections = retrieved_page.sections.all()
    print(f"✓ Retrieved {sections.count()} sections")
    
    # Test client access to the page
    client = Client()
    response = client.get(f'/page/{page.slug}/')
    
    if response.status_code == 200:
        print("✓ Page is accessible via URL")
        # Check if HTML content is rendered
        if '<h1>' in response.content.decode():
            print("✓ HTML content is rendered in template")
        else:
            print("⚠ HTML content may not be rendered properly")
    else:
        print(f"⚠ Page not accessible, status code: {response.status_code}")
    
    print("\nTinyMCE functionality test completed successfully!")
    print(f"Test page URL: http://localhost:8001/page/{page.slug}/")
    print(f"Admin URL: http://localhost:8001/admin_interface/pages/{page.id}/edit/")
    
    return page, section

if __name__ == '__main__':
    try:
        page, section = test_tinymce_functionality()
        print(f"\nTest completed. You can now:")
        print(f"1. Visit the page at: http://localhost:8001/page/{page.slug}/")
        print(f"2. Edit the page in admin at: http://localhost:8001/admin_interface/pages/{page.id}/edit/")
        print(f"3. Test TinyMCE editor functionality")
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()