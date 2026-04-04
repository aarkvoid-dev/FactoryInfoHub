#!/usr/bin/env python
"""
Script to create dummy data for FactoryInfoHub project.
Creates a superuser and optional sample data.

Usage:
    python manage.py shell < scripts/create_dummy_data.py
    
Or run directly:
    python scripts/create_dummy_data.py
"""

import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FactoryInfoHub.settings')
django.setup()

from django.contrib.auth.models import User
from Accounts.models import Profile
from location.models import Country, State, District
from category.models import Category
from blog.models import Post
from Karkahan.models import Factory
from Workers.models import Worker
from faq.models import FAQ, FAQCategory


def create_superuser():
    """Create a superuser account."""
    print("Creating superuser...")
    
    # Check if superuser already exists
    if User.objects.filter(username='admin').exists():
        print("Superuser 'admin' already exists.")
        return User.objects.get(username='admin')
    
    # Create superuser
    user = User.objects.create_superuser(
        username='admin',
        email='admin@factoryinfohub.com',
        password='Admin@123456',
        first_name='Super',
        last_name='Admin'
    )
    
    # Create profile for superuser
    Profile.objects.get_or_create(
        user=user,
        defaults={
            'phone': '+91 9876543210',
            'is_verified': True,
        }
    )
    
    print(f"Superuser created: username='admin', password='Admin@123456'")
    return user


def create_location_data():
    """Create sample location data."""
    print("\nCreating location data...")
    
    # Create India
    india, created = Country.objects.get_or_create(
        name='India',
        code='IN',
        defaults={'name_hi': 'भारत'}
    )
    
    # Create Maharashtra
    maharashtra, created = State.objects.get_or_create(
        country=india,
        name='Maharashtra',
        defaults={'name_hi': 'महाराष्ट्र', 'code': 'MH'}
    )
    
    # Create Mumbai
    mumbai, created = District.objects.get_or_create(
        state=maharashtra,
        name='Mumbai',
        defaults={'name_hi': 'मुंबई'}
    )
    
    # Create Pune
    pune, created = District.objects.get_or_create(
        state=maharashtra,
        name='Pune',
        defaults={'name_hi': 'पुणे'}
    )
    
    print(f"Location data created: India > Maharashtra > Mumbai, Pune")


def create_category_data():
    """Create sample category data."""
    print("\nCreating category data...")
    
    categories = [
        {'name': 'Textile', 'name_hi': 'कपड़ा', 'description': 'Textile and fabric manufacturing'},
        {'name': 'Automotive', 'name_hi': 'ऑटोमोटिव', 'description': 'Automotive parts and manufacturing'},
        {'name': 'Electronics', 'name_hi': 'इलेक्ट्रॉनिक्स', 'description': 'Electronics and technology'},
        {'name': 'Pharmaceuticals', 'name_hi': 'फार्मास्यूटिकल्स', 'description': 'Pharmaceutical and healthcare'},
        {'name': 'Food Processing', 'name_hi': 'खाद्य प्रसंस्करण', 'description': 'Food and beverage processing'},
        {'name': 'Chemicals', 'name_hi': 'रसायन', 'description': 'Chemical manufacturing'},
        {'name': 'Metal Works', 'name_hi': 'धातु कार्य', 'description': 'Metal fabrication and works'},
        {'name': 'Plastics', 'name_hi': 'प्लास्टिक', 'description': 'Plastic manufacturing and products'},
    ]
    
    for cat_data in categories:
        Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'name_hi': cat_data['name_hi'],
                'description': cat_data['description'],
                'slug': cat_data['name'].lower().replace(' ', '-')
            }
        )
    
    print(f"Created {len(categories)} categories")


def create_factory_data(user):
    """Create sample factory data."""
    print("\nCreating factory data...")
    
    try:
        category = Category.objects.first()
        if not category:
            print("No categories found. Run create_category_data() first.")
            return
        
        district = District.objects.first()
        if not district:
            print("No districts found. Run create_location_data() first.")
            return
        
        factories = [
            {
                'name': 'ABC Textiles Pvt Ltd',
                'name_hi': 'एबीसी टेक्सटाइल्स प्राइवेट लिमिटेड',
                'description': 'Leading textile manufacturer specializing in cotton fabrics and garments.',
                'description_hi': 'कपड़ा और परिधान में विशेषज्ञता प्राप्त प्रमुख कपड़ा निर्माता।',
                'category': category,
                'district': district,
                'address': 'Plot No. 123, MIDC Industrial Area, Mumbai',
                'contact_number': '+91 9876543211',
                'contact_email': 'info@abctextiles.com',
                'website': 'https://abctextiles.com',
                'established_year': 2005,
                'employee_count': 250,
                'owner': user,
            },
            {
                'name': 'XYZ Automotive Components',
                'name_hi': 'XYZ ऑटोमोटिव घटक',
                'description': 'Precision automotive parts manufacturer for leading car companies.',
                'description_hi': 'प्रमुख कार कंपनियों के लिए सटीक ऑटोमोटिव पुर्जे निर्माता।',
                'category': category,
                'district': district,
                'address': 'Survey No. 456, Industrial Estate, Pune',
                'contact_number': '+91 9876543212',
                'contact_email': 'contact@xyzauto.com',
                'website': 'https://xyzauto.com',
                'established_year': 2010,
                'employee_count': 180,
                'owner': user,
            },
        ]
        
        for factory_data in factories:
            Factory.objects.get_or_create(
                name=factory_data['name'],
                defaults=factory_data
            )
        
        print(f"Created {len(factories)} factories")
    except Exception as e:
        print(f"Error creating factory data: {e}")


def create_worker_data():
    """Create sample worker data."""
    print("\nCreating worker data...")
    
    try:
        factory = Factory.objects.first()
        if not factory:
            print("No factories found. Run create_factory_data() first.")
            return
        
        workers = [
            {
                'name': 'Rajesh Kumar',
                'name_hi': 'राजेश कुमार',
                'father_name': 'Mohan Kumar',
                'father_name_hi': 'मोहन कुमार',
                'aadhar_number': '123456789012',
                'mobile': '+91 9876543213',
                'address': 'Room No. 12, Worker Colony, Mumbai',
                'date_of_birth': '1985-05-15',
                'gender': 'Male',
                'education': '10th Pass',
                'education_hi': '10वीं पास',
                'experience': '8 years',
                'experience_hi': '8 साल',
                'skills': 'Machine Operation, Quality Control',
                'skills_hi': 'मशीन संचालन, गुणवत्ता नियंत्रण',
                'factory': factory,
            },
            {
                'name': 'Sunita Devi',
                'name_hi': 'सुनीता देवी',
                'father_name': 'Ram Prasad',
                'father_name_hi': 'राम प्रसाद',
                'aadhar_number': '123456789013',
                'mobile': '+91 9876543214',
                'address': 'Room No. 15, Worker Colony, Mumbai',
                'date_of_birth': '1990-08-20',
                'gender': 'Female',
                'education': '12th Pass',
                'education_hi': '12वीं पास',
                'experience': '5 years',
                'experience_hi': '5 साल',
                'skills': 'Assembly, Packaging',
                'skills_hi': 'असेंबली, पैकेजिंग',
                'factory': factory,
            },
        ]
        
        for worker_data in workers:
            Worker.objects.get_or_create(
                name=worker_data['name'],
                defaults=worker_data
            )
        
        print(f"Created {len(workers)} workers")
    except Exception as e:
        print(f"Error creating worker data: {e}")


def create_blog_data(user):
    """Create sample blog posts."""
    print("\nCreating blog data...")
    
    try:
        posts = [
            {
                'title': 'Welcome to FactoryInfoHub',
                'slug': 'welcome-to-factoryinfohub',
                'content': '''
                    <h2>About FactoryInfoHub</h2>
                    <p>FactoryInfoHub is your one-stop platform for discovering and connecting with manufacturing units across India. We aim to bridge the gap between manufacturers and buyers, creating a transparent and efficient ecosystem.</p>
                    
                    <h3>Our Mission</h3>
                    <p>To empower small and medium-scale manufacturers by providing them with a digital platform to showcase their capabilities and connect with potential buyers worldwide.</p>
                    
                    <h3>Key Features</h3>
                    <ul>
                        <li>Comprehensive factory database</li>
                        <li>Detailed worker information</li>
                        <li>Category-wise classification</li>
                        <li>Location-based search</li>
                        <li>Real-time updates</li>
                    </ul>
                ''',
                'excerpt': 'Welcome to FactoryInfoHub - your gateway to India\'s manufacturing ecosystem.',
                'author': user,
                'status': 'published',
            },
            {
                'title': 'How to Use FactoryInfoHub Effectively',
                'slug': 'how-to-use-factoryinfohub-effectively',
                'content': '''
                    <h2>Getting Started with FactoryInfoHub</h2>
                    <p>FactoryInfoHub offers a comprehensive platform for exploring India's manufacturing landscape. Here's how to make the most of it:</p>
                    
                    <h3>For Buyers</h3>
                    <ol>
                        <li><strong>Search by Category:</strong> Use our category filter to find manufacturers in your specific industry.</li>
                        <li><strong>Location-based Search:</strong> Find factories near your location to reduce logistics costs.</li>
                        <li><strong>Verify Credentials:</strong> Check factory details, employee count, and establishment year.</li>
                        <li><strong>Contact Directly:</strong> Use the provided contact information to reach out to manufacturers.</li>
                    </ol>
                    
                    <h3>For Manufacturers</h3>
                    <ol>
                        <li><strong>Create Detailed Profile:</strong> Provide comprehensive information about your capabilities.</li>
                        <li><strong>Update Regularly:</strong> Keep your factory information current.</li>
                        <li><strong>Add Photos:</strong> Showcase your infrastructure and products.</li>
                        <li><strong>Respond Promptly:</strong> Reply to inquiries in a timely manner.</li>
                    </ol>
                ''',
                'excerpt': 'Learn how to effectively use FactoryInfoHub to connect with manufacturers and buyers.',
                'author': user,
                'status': 'published',
            },
        ]
        
        for post_data in posts:
            Post.objects.get_or_create(
                slug=post_data['slug'],
                defaults=post_data
            )
        
        print(f"Created {len(posts)} blog posts")
    except Exception as e:
        print(f"Error creating blog data: {e}")


def create_faq_data():
    """Create sample FAQ data."""
    print("\nCreating FAQ data...")
    
    try:
        # Create FAQ categories
        categories = [
            {'name': 'General', 'name_hi': 'सामान्य', 'description': 'General questions about FactoryInfoHub'},
            {'name': 'For Manufacturers', 'name_hi': 'निर्माताओं के लिए', 'description': 'Questions for factory owners and manufacturers'},
            {'name': 'For Buyers', 'name_hi': 'खरीदारों के लिए', 'description': 'Questions for buyers and purchasers'},
        ]
        
        faq_categories = []
        for cat_data in categories:
            cat, created = FAQCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'name_hi': cat_data['name_hi'],
                    'description': cat_data['description'],
                    'slug': cat_data['name'].lower().replace(' ', '-')
                }
            )
            faq_categories.append(cat)
        
        # Create FAQs
        faqs = [
            {
                'question': 'What is FactoryInfoHub?',
                'question_hi': 'FactoryInfoHub क्या है?',
                'answer': 'FactoryInfoHub is a comprehensive platform that provides information about manufacturing units across India, including their capabilities, workforce, and contact details.',
                'answer_hi': 'FactoryInfoHub एक व्यापक मंच है जो भारत भर में विनिर्माण इकाइयों के बारे में जानकारी प्रदान करता है, जिसमें उनकी क्षमताएं, कार्यबल और संपर्क विवरण शामिल हैं।',
                'category': faq_categories[0],
                'order': 1,
            },
            {
                'question': 'How can I register my factory?',
                'question_hi': 'मैं अपनी फैक्ट्री कैसे पंजीकृत कर सकता हूं?',
                'answer': 'You can register your factory by creating an account on FactoryInfoHub and submitting your factory details through the registration form. Our team will verify the information before publishing.',
                'answer_hi': 'आप FactoryInfoHub पर खाता बनाकर और पंजीकरण फ़ॉर्म के माध्यम से अपनी फैक्ट्री का विवरण जमा करके अपनी फैक्ट्री पंजीकृत कर सकते हैं। प्रकाशित करने से पहले हमारी टीम जानकारी की पुष्टि करेगी।',
                'category': faq_categories[1],
                'order': 2,
            },
            {
                'question': 'Is it free to use FactoryInfoHub?',
                'question_hi': 'FactoryInfoHub का उपयोग करना मुफ्त है?',
                'answer': 'Yes, basic usage of FactoryInfoHub is completely free. We offer premium features for manufacturers who want enhanced visibility and additional tools.',
                'answer_hi': 'हाँ, FactoryInfoHub का बुनियादी उपयोग पूरी तरह से मुफ्त है। हम उन निर्माताओं के लिए प्रीमियम सुविधाएं प्रदान करते हैं जो बेहतर दृश्यता और अतिरिक्त उपकरण चाहते हैं।',
                'category': faq_categories[2],
                'order': 3,
            },
        ]
        
        for faq_data in faqs:
            FAQ.objects.get_or_create(
                question=faq_data['question'],
                defaults=faq_data
            )
        
        print(f"Created {len(faqs)} FAQs in {len(faq_categories)} categories")
    except Exception as e:
        print(f"Error creating FAQ data: {e}")


def main():
    """Main function to create all dummy data."""
    print("=" * 60)
    print("FactoryInfoHub Dummy Data Generator")
    print("=" * 60)
    
    # Create superuser first
    admin_user = create_superuser()
    
    # Create location data
    create_location_data()
    
    # Create category data
    create_category_data()
    
    # Create factory data
    create_factory_data(admin_user)
    
    # Create worker data
    create_worker_data()
    
    # Create blog data
    create_blog_data(admin_user)
    
    # Create FAQ data
    create_faq_data()
    
    print("\n" + "=" * 60)
    print("Dummy data creation completed!")
    print("=" * 60)
    print("\nSuperuser credentials:")
    print("  Username: admin")
    print("  Password: Admin@123456")
    print("\nYou can now log in to the admin panel at /admin/")


if __name__ == '__main__':
    main()