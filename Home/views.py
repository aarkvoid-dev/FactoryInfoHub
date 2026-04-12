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
def contact(request, type='enquiry'):
    valid_types = ['enquiry', 'export', 'karigar', 'online_class']
    if type not in valid_types:
        type = 'enquiry'
    
    # Helper to build common context
    def get_base_context(additional=None):
        context = {
            'type': type,
            'title': dict(ContactMessage.INQUIRY_TYPES).get(type, 'Contact Us'),
            'user_name': 'User',
            'user_email': '',
            'user_country_code': '+91',
            'user_mobile': '',
        }
        if request.user.is_authenticated:
            context['user_email'] = request.user.email
            context['user_name'] = request.user.get_full_name() or request.user.username
            if hasattr(request.user, 'profile') and request.user.profile.phone_number:
                phone = request.user.profile.phone_number
                if phone.startswith('+91'):
                    context['user_country_code'] = '+91'
                    context['user_mobile'] = phone[3:].strip()
                else:
                    context['user_country_code'] = '+91'
                    context['user_mobile'] = phone
        if additional:
            context.update(additional)
        context['pages'] = Page.objects.filter(is_published=True, is_deleted=False).order_by('title')
        return context

    if request.method == 'POST':
        inquiry_type = request.POST.get('type', type)
        
        name = request.POST.get('name')
        email = request.POST.get('email')
        country_code = request.POST.get('country_code', '+91')
        mobile_number = request.POST.get('mobile_number', '')
        message = request.POST.get('message')
        brand_name = request.POST.get('brand_name', '')
        subject = request.POST.get('subject', '')
        
        if not all([name, email, message]):
            messages.error(request, 'Please fill in all required fields.')
            # Re-render with submitted data
            context = get_base_context({
                'name': name,
                'email': email,
                'brand_name': brand_name,
                'mobile_number': mobile_number,
                'message': message,
                'country_code': country_code,
            })
            return render(request, 'home/contact.html', context)
        
        full_mobile = f"{country_code} {mobile_number}" if mobile_number else ''
        
        try:
            contact_message = ContactMessage.objects.create(
                type=inquiry_type,
                name=name,
                brand_name=brand_name,
                email=email,
                mobile_number=full_mobile,
                subject=subject or f"{dict(ContactMessage.INQUIRY_TYPES).get(inquiry_type, 'Enquiry')} - {name}",
                message=message,
                user=request.user if request.user.is_authenticated else None
            )
            
            # Email notifications (unchanged)...
            try:
                admin_subject = f"New {dict(ContactMessage.INQUIRY_TYPES).get(inquiry_type, 'Contact')} from {name}"
                admin_message = f"""..."""
                admin_recipients = getattr(settings, 'CONTACT_EMAIL_RECIPIENTS', [settings.DEFAULT_FROM_EMAIL])
                send_mail(admin_subject, admin_message, settings.DEFAULT_FROM_EMAIL, admin_recipients, fail_silently=False)
                
                user_subject = "Thank you for contacting FactoryInfoHub"
                user_message = f"""..."""
                send_mail(user_subject, user_message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
            except Exception as e:
                print(f"Email error: {e}")
            
            messages.success(request, 'Your message has been sent successfully!')
            # return redirect('contact', type=inquiry_type)
        except Exception as e:
            messages.error(request, f'An error occurred. Please try again later,{e}')
            context = get_base_context({
                'name': name,
                'email': email,
                'brand_name': brand_name,
                'mobile_number': mobile_number,
                'message': message,
                'country_code': country_code,
            })
            return render(request, 'home/contact.html', context)
    
    # GET request
    context = get_base_context()
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
