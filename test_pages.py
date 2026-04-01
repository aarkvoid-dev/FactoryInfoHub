#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, '/Users/arfatulshaikh/Projects/InfoHub/FactoryInfoHub')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

from Home.models import Page

print("Testing Page model...")
print(f"Total pages in database: {Page.objects.count()}")

for page in Page.objects.all():
    print(f"- {page.title} ({page.slug}) - Published: {page.is_published}")
    print(f"  Sections: {page.sections.count()}")
    print(f"  Type: {page.get_page_type_display()}")
    print()

print("Test completed successfully!")