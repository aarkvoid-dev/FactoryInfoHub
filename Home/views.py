from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.utils import timezone
from Karkahan.models import Factory
from blog.models import BlogPost
from category.models import Category
from location.models import Country,City
from .models import HomePageVideo, ContactMessage,Page
from Accounts.decorators import profile_complete_required

def home(request):
    # Fetch featured factories (verified and active)
    featured_factories = Factory.objects.filter(
        is_verified=True,
        is_active=True,
        is_deleted=False
    ).order_by('-created_at')[:10]

    # Fetch latest blog posts
    latest_posts = BlogPost.objects.filter(
        is_published=True,
        is_deleted=False
    ).order_by('-created_at')[:10]

    # Get category statistics
    category_stats = Category.objects.annotate(
        factory_count=Count('factories', filter=Q(factories__is_deleted=False, factories__is_active=True))
    ).order_by('?')   # '?' means random order

    # Get all cities, randomly ordered
    city_stats = City.objects.annotate(
        factory_count=Count('factories', filter=Q(factories__is_deleted=False, factories__is_active=True))
    ).order_by('?')

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

    # Get all published pages for footer
    # pages = Page.objects.filter(is_published=True, is_deleted=False).order_by('title')
    
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
        # 'pages': pages,
    }
    return render(request, 'home/home.html', context)

@profile_complete_required
def contact(request):
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        country_code = request.POST.get('country_code', '+91')
        mobile_number = request.POST.get('mobile_number', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Combine country code with mobile number for storage
        full_mobile_number = f"{country_code} {mobile_number}" if mobile_number else ''
        
        # Validate required fields
        if not all([name, email, subject, message]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'home/contact.html', {
                'name': name,
                'email': email,
                'country_code': country_code,
                'mobile_number': mobile_number,
                'subject': subject,
                'message': message
            })
        
        try:
            # Save contact message to database
            contact_message = ContactMessage.objects.create(
                name=name,
                email=email,
                mobile_number=full_mobile_number,
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
Mobile Number: {full_mobile_number if full_mobile_number else 'Not provided'}
Subject: {subject}
User: {request.user.username if request.user.is_authenticated else 'Anonymous'}
Date: {contact_message.created_at.strftime('%Y-%m-%d %H:%M:%S %Z')}

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
        # Get mobile number from user profile if available
        if hasattr(request.user, 'profile') and request.user.profile.phone_number:
            phone = request.user.profile.phone_number
            # Extract country code and number
            if phone.startswith('+91'):
                context['user_country_code'] = '+91'
                context['user_mobile'] = phone[3:].strip()
            elif phone.startswith('+1'):
                context['user_country_code'] = '+1'
                context['user_mobile'] = phone[2:].strip()
            elif phone.startswith('+44'):
                context['user_country_code'] = '+44'
                context['user_mobile'] = phone[3:].strip()
            else:
                context['user_country_code'] = '+91'  # Default
                context['user_mobile'] = phone
    
    # Add pages for footer
    context['pages'] = Page.objects.filter(is_published=True, is_deleted=False).order_by('title')
    
    return render(request, 'home/contact.html', context)

def products(request):
    """Products page - Coming Soon"""
    return render(request, 'home/products.html')

def terms_and_conditions(request):
    """Terms and Conditions page"""
    return render(request, 'terms_and_conditions.html')

def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, 'privacy_policy.html')

def about_us(request):
    """About Us page"""
    return render(request, 'about_us.html')

def disclaimer(request):
    """Disclaimer page"""
    return render(request, 'disclaimer.html')

def refund_policy(request):
    """Refund Policy page"""
    return render(request, 'refund_policy.html')


def page_detail(request, slug):
    """Dynamic page view for Terms, Refund Policy, Disclaimer, etc."""
    page = get_object_or_404(Page, slug=slug, is_published=True, is_deleted=False)
    
    # Get page sections if they exist
    sections = page.sections.filter(is_deleted=False).order_by('order')
    
    context = {
        'page': page,
        'sections': sections,
    }
    
    # Use a generic page template or specific templates based on page type
    # template_name = f'pages/{page.page_type}.html'
    
    # Check if specific template exists, otherwise use generic
    # try:
    #     return render(request, template_name, context)
    # except:
    #     # Fallback to generic page template
    #     return render(request, 'pages/page.html', context)

    return render(request, 'page.html', context)


def terms_and_conditions_view(request):
    """Legacy view for Terms & Conditions - redirects to dynamic page"""
    page = Page.get_page_by_type('terms')
    if page:
        return redirect('page_detail', slug=page.slug)
    return render(request, 'terms_and_conditions.html')


def refund_policy_view(request):
    """Legacy view for Refund Policy - redirects to dynamic page"""
    page = Page.get_page_by_type('refund')
    if page:
        return redirect('page_detail', slug=page.slug)
    return render(request, 'refund_policy.html')


def disclaimer_view(request):
    """Legacy view for Disclaimer - redirects to dynamic page"""
    page = Page.get_page_by_type('disclaimer')
    if page:
        return redirect('page_detail', slug=page.slug)
    return render(request, 'disclaimer.html')


def privacy_policy_view(request):
    """Legacy view for Privacy Policy - redirects to dynamic page"""
    page = Page.get_page_by_type('privacy')
    if page:
        return redirect('page_detail', slug=page.slug)
    return render(request, 'privacy_policy.html')


def about_us_view(request):
    """Legacy view for About Us - redirects to dynamic page"""
    page = Page.get_page_by_type('about')
    if page:
        return redirect('page_detail', slug=page.slug)
    return render(request, 'about_us.html')
