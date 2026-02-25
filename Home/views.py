from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from Karkahan.models import Factory
from blog.models import BlogPost
from category.models import Category
from location.models import Country,City
from .models import HomePageVideo, ContactMessage

def home(request):
    # Fetch featured factories (verified and active)
    featured_factories = Factory.objects.filter(
        is_verified=True,
        is_active=True,
        is_deleted=False
    ).order_by('-created_at')[:3]

    # Fetch latest blog posts
    latest_posts = BlogPost.objects.filter(
        is_published=True,
        is_deleted=False
    ).order_by('-created_at')[:3]

    # Get category statistics
    category_stats = Category.objects.annotate(
        factory_count=Count('factories', filter=Q(factories__is_deleted=False, factories__is_active=True))
    ).order_by('-factory_count')[:4]

    # Get city statistics
    city_stats = City.objects.annotate(
        factory_count=Count('factories', filter=Q(factories__is_deleted=False, factories__is_active=True))
    ).order_by('-factory_count')[:8]

    # Get overall statistics
    total_factories = Factory.objects.filter(is_deleted=False).count()
    active_factories = Factory.objects.filter(is_active=True, is_deleted=False).count()
    verified_factories = Factory.objects.filter(is_verified=True, is_deleted=False).count()
    categories_with_factories = Category.objects.filter(
        factories__isnull=False,
        factories__is_deleted=False
    ).distinct().count()
    countries_covered = Country.objects.filter(
        factories__isnull=False,
        factories__is_deleted=False
    ).distinct().count()
    cities_covered = City.objects.filter(
        factories__isnull=False,
        factories__is_deleted=False
    ).distinct().count()

    # Get total monthly capacity (if available)
    total_capacity = Factory.objects.filter(is_deleted=False).aggregate(
        total_capacity=Sum('annual_turnover')
    )['total_capacity'] or 0

    context = {
        'featured_factories': featured_factories,
        'latest_posts': latest_posts,
        'category_stats': category_stats,
        'city_stats': city_stats,
        'total_factories': total_factories,
        'active_factories': active_factories,
        'verified_factories': verified_factories,
        'categories_with_factories': categories_with_factories,
        'countries_covered': countries_covered,
        'total_capacity': total_capacity,
        'home_page_video': HomePageVideo.objects.filter(is_active=True).first(),
    }
    return render(request, 'home/home.html', context)

def contact(request):
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Validate required fields
        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'home/contact.html', {
                'name': name,
                'email': email,
                'subject': subject,
                'message': message
            })
        
        try:
            # Save contact message to database
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject,
                message=message,
                user=request.user if request.user.is_authenticated else None
            )
            
            # Send email notification
            try:
                # Email to admin team
                admin_subject = f"New Contact Form Submission: {subject}"
                admin_message = f"""
New contact form submission received:

Name: {name}
Email: {email}
Subject: {subject}
User: {request.user.username if request.user.is_authenticated else 'Anonymous'}
Date: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Message:
{message}

---
This message was sent from FactoryInfoHub contact form.
"""
                
                # Send to admin email (you can configure this in settings)
                admin_recipients = getattr(settings, 'CONTACT_EMAIL_RECIPIENTS', [settings.DEFAULT_FROM_EMAIL])
                send_mail(
                    admin_subject,
                    admin_message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_recipients,
                    fail_silently=False,
                )
                
                # Send confirmation email to user
                user_subject = "Thank you for your message!"
                user_message = f"""
Dear {name},

Thank you for contacting FactoryInfoHub! 

We have received your message and will get back to you within 24 hours.

Your message details:
Subject: {subject}
Message: {message[:200]}{'...' if len(message) > 200 else ''}

Best regards,
FactoryInfoHub Team

---
If you have any urgent inquiries, please contact us at:
Email: support@factoryinfohub.com
Phone: +91 22 1234 5678
"""
                
                send_mail(
                    user_subject,
                    user_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=True,  # Don't fail if user email is invalid
                )
                
            except Exception as email_error:
                # Log email error but don't fail the form submission
                print(f"Email sending failed: {email_error}")
                # You could also use Django's logging here
            
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('contact')
            
        except Exception as e:
            messages.error(request, 'Sorry, there was an error submitting your message. Please try again.')
            return render(request, 'home/contact.html', {
                'name': name,
                'email': email,
                'subject': subject,
                'message': message
            })
    
    # For GET requests, prepare context with user info if logged in
    context = {}
    if request.user.is_authenticated:
        context['user_email'] = request.user.email
    
    return render(request, 'home/contact.html', context)
