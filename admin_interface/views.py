from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse, JsonResponse
import csv
import json
from django.contrib.auth.models import User
from Workers.models import Worker, WorkExperience
from Karkahan.models import Factory, FactoryImage,Order,PaymentGateway,OrderItem,Cart,FactoryViewTracker,FactoryViewStats
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from blog.models import BlogPost, BlogImage
from Accounts.models import Profile
from Home.models import ContactMessage, HomePageVideo, ContactReply, Page, PageSection
from .models import PaymentIssueReport
from .forms import AdminUserForm, AdminFactoryForm, AdminWorkerForm, AdminBlogForm, AdminBlogImageForm, AdminLocationForm, AdminCategoryForm, AdminCountryForm, AdminStateForm, AdminCityForm, AdminDistrictForm, AdminRegionForm, AdminSubCategoryForm, AdminFAQQuestionForm, AdminHomePageVideoForm, AdminPaymentGatewayForm, AdminPageForm, AdminPageSectionForm
from faq.models import FAQQuestion
from Karkahan.views import send_order_receipt
from django.db import transaction
from django.core.paginator import Paginator
import copy
from django.core.exceptions import ValidationError


def and_search_filter(queryset, search_terms, fields):
    """
    Apply AND search across multiple fields.
    search_terms: list of strings (words)
    fields: list of field names (e.g., ['username', 'email'])
    """
    from django.db.models import Q
    if not search_terms:
        return queryset
    q_objects = Q()
    for term in search_terms:
        term_q = Q()
        for field in fields:
            term_q |= Q(**{f"{field}__icontains": term})
        q_objects &= term_q
    return queryset.filter(q_objects)


@login_required
def admin_dashboard(request):
    # Get user role
    profile = request.user.profile
    role = profile.role

    # Check if user has admin access
    if role != 'admin' and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # Get statistics
    user_count = User.objects.count()
    factory_count = Factory.objects.count()
    worker_count = Worker.objects.count()
    contact_count = ContactMessage.objects.filter(is_deleted=False).count()

    # Get today's counts
    today = datetime.now().date()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_factories_today = Factory.objects.filter(created_at__date=today).count()
    new_workers_today = Worker.objects.filter(created_at__date=today).count()
    new_contacts_today = ContactMessage.objects.filter(created_at__date=today, is_deleted=False).count()

    # Get pending reports (unread contact messages)
    pending_reports = ContactMessage.objects.filter(is_read=False, is_deleted=False).count()

    # Get recent activities
    recent_activities = []

    # Add user creation activities
    recent_user_creations = User.objects.filter(
        date_joined__gte=today - timedelta(days=7)
    ).order_by('-date_joined')[:5]

    for user in recent_user_creations:
        recent_activities.append({
            'type': 'user_created',
            'message': f'User {user.username} created',
            'timestamp': user.date_joined,
            'icon': 'fas fa-user-plus',
            'color': 'text-primary'
        })

    # Add factory creation activities
    recent_factory_creations = Factory.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]

    for factory in recent_factory_creations:
        recent_activities.append({
            'type': 'factory_created',
            'message': f'Factory {factory.name} created',
            'timestamp': factory.created_at,
            'icon': 'fas fa-industry',
            'color': 'text-success'
        })

    # Add worker creation activities
    recent_worker_creations = Worker.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]

    for worker in recent_worker_creations:
        recent_activities.append({
            'type': 'worker_created',
            'message': f'Worker {worker.full_name} created',
            'timestamp': worker.created_at,
            'icon': 'fas fa-user-tie',
            'color': 'text-warning'
        })

    # Add contact message activities
    recent_contacts = ContactMessage.objects.filter(
        created_at__gte=today - timedelta(days=7),
        is_deleted=False
    ).order_by('-created_at')[:5]

    for contact in recent_contacts:
        recent_activities.append({
            'type': 'contact_message',
            'message': f'New message from {contact.name}: {contact.subject}',
            'timestamp': contact.created_at,
            'icon': 'fas fa-envelope',
            'color': 'text-info'
        })

    # Add blog post activities
    recent_blogs = BlogPost.objects.filter(
        created_at__gte=today - timedelta(days=7),
        is_deleted=False
    ).order_by('-created_at')[:5]

    for blog in recent_blogs:
        recent_activities.append({
            'type': 'blog_created',
            'message': f'Blog post "{blog.title}" published',
            'timestamp': blog.created_at,
            'icon': 'fas fa-file-alt',
            'color': 'text-secondary'
        })

    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]

    # Calculate infrastructure status
    from django.db import connection
    
    try:
        # Database connection test
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "Connected"
            db_health = 100
    except:
        db_status = "Disconnected"
        db_health = 0

    # Storage usage (simplified - using a default value since psutil is not available)
    storage_percentage = 50  # Default value when psutil is not available

    # System uptime (simplified)
    system_uptime = "24/7"  # This would need more complex implementation

    context = {
        'user_count': user_count,
        'factory_count': factory_count,
        'worker_count': worker_count,
        'contact_count': contact_count,
        'pending_reports': pending_reports,
        'new_users_today': new_users_today,
        'new_factories_today': new_factories_today,
        'new_workers_today': new_workers_today,
        'new_contacts_today': new_contacts_today,
        'recent_activities': recent_activities,
        'db_status': db_status,
        'db_health': db_health,
        'storage_percentage': storage_percentage,
        'system_uptime': system_uptime,
        'unread_messages': ContactMessage.objects.filter(is_read=False, is_deleted=False).count(),
        'pending_verifications': User.objects.filter(profile__email_verified=False).count(),
    }

    return render(request, 'CustomAdmin/dashboard/dashboard.html', context)


@login_required
def admin_dashboard_api(request):
    """API endpoint for dashboard data refresh"""
    # Get user role
    profile = request.user.profile
    role = profile.role

    # Check if user has admin access
    if role != 'admin' and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # Get statistics
    user_count = User.objects.count()
    factory_count = Factory.objects.count()
    worker_count = Worker.objects.count()
    contact_count = ContactMessage.objects.filter(is_deleted=False).count()

    # Get today's counts
    today = datetime.now().date()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_factories_today = Factory.objects.filter(created_at__date=today).count()
    new_workers_today = Worker.objects.filter(created_at__date=today).count()
    new_contacts_today = ContactMessage.objects.filter(created_at__date=today, is_deleted=False).count()

    # Get pending reports (unread contact messages)
    pending_reports = ContactMessage.objects.filter(is_read=False, is_deleted=False).count()

    # Get recent activities (last 5)
    recent_activities = []

    # Add user creation activities
    recent_user_creations = User.objects.filter(
        date_joined__gte=today - timedelta(days=7)
    ).order_by('-date_joined')[:5]

    for user in recent_user_creations:
        recent_activities.append({
            'type': 'user_created',
            'message': f'User {user.username} created',
            'timestamp': user.date_joined.isoformat(),
            'icon': 'fas fa-user-plus',
            'color': 'text-primary'
        })

    # Add factory creation activities
    recent_factory_creations = Factory.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]

    for factory in recent_factory_creations:
        recent_activities.append({
            'type': 'factory_created',
            'message': f'Factory {factory.name} created',
            'timestamp': factory.created_at.isoformat(),
            'icon': 'fas fa-industry',
            'color': 'text-success'
        })

    # Add worker creation activities
    recent_worker_creations = Worker.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]

    for worker in recent_worker_creations:
        recent_activities.append({
            'type': 'worker_created',
            'message': f'Worker {worker.full_name} created',
            'timestamp': worker.created_at.isoformat(),
            'icon': 'fas fa-user-tie',
            'color': 'text-warning'
        })

    # Add contact message activities
    recent_contacts = ContactMessage.objects.filter(
        created_at__gte=today - timedelta(days=7),
        is_deleted=False
    ).order_by('-created_at')[:5]

    for contact in recent_contacts:
        recent_activities.append({
            'type': 'contact_message',
            'message': f'New message from {contact.name}: {contact.subject}',
            'timestamp': contact.created_at.isoformat(),
            'icon': 'fas fa-envelope',
            'color': 'text-info'
        })

    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]

    # Calculate infrastructure status
    from django.db import connection
    
    try:
        # Database connection test
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_status = "Connected"
            db_health = 100
    except:
        db_status = "Disconnected"
        db_health = 0

    # Storage usage (simplified - using a default value since psutil is not available)
    storage_percentage = 50  # Default value when psutil is not available

    data = {
        'kpi': {
            'user_count': user_count,
            'factory_count': factory_count,
            'worker_count': worker_count,
            'contact_count': contact_count,
            'pending_reports': pending_reports,
            'new_users_today': new_users_today,
            'new_factories_today': new_factories_today,
            'new_workers_today': new_workers_today,
            'new_contacts_today': new_contacts_today,
        },
        'activities': recent_activities,
        'infrastructure': {
            'db_status': db_status,
            'db_health': db_health,
            'storage_percentage': storage_percentage,
            'unread_messages': ContactMessage.objects.filter(is_read=False, is_deleted=False).count(),
            'pending_verifications': User.objects.filter(profile__email_verified=False).count(),
        }
    }

    return JsonResponse(data)

@login_required
def admin_users(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # Get all filter parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')
    status_filter = request.GET.get('status', '')

    users = User.objects.select_related('profile').all()

    # Apply search filter (from base navbar OR filter form)
    if search_query:
        terms = search_query.split()
        users = and_search_filter(
            users,
            terms,
            ['username', 'email', 'first_name', 'last_name', 'profile__phone_number']
        )

    # Apply role filter
    if role_filter:
        users = users.filter(profile__role=role_filter)

    # Apply status filter (active / inactive)
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)

    # Order by most recent first
    users = users.order_by('-date_joined')

    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }
    return render(request, 'CustomAdmin/users/users.html', context)

@login_required
def admin_user_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        is_active = 'is_active' in request.POST
        role = request.POST.get('role', 'user')
        

        # Validation
        if not username or not email or not password:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'CustomAdmin/users/user_form.html', {
                'action': 'create',
                'title': 'Create New User'
            })

        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'CustomAdmin/users/user_form.html', {
                'action': 'create',
                'title': 'Create New User'
            })

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'CustomAdmin/users/user_form.html', {
                'action': 'create',
                'title': 'Create New User'
            })

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'CustomAdmin/users/user_form.html', {
                'action': 'create',
                'title': 'Create New User'
            })

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active
        )

        # Create profile for all users, including superusers
        try:
            Profile.objects.create(
                user=user,
                role=role,
                email_notifications=True,
                in_app_notifications=True
            )
        except Exception as e:
            # Log the error and create a fallback profile with minimal settings
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to create Profile for user {username}: {e}")
            
            # Create a basic profile as fallback
            Profile.objects.create(
                user=user,
                role=role,
                email_notifications=False,
                in_app_notifications=False
            )
            messages.warning(request, f'Profile created with default settings due to an error: {e}')

        messages.success(request, f'User "{user.username}" created successfully!')
        return redirect('admin_interface:admin_users')
    else:
        context = {
            'action': 'create',
            'title': 'Create New User'
        }
        return render(request, 'CustomAdmin/users/user_form.html', context)

@login_required
def admin_user_edit(request, user_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # Use select_related to ensure profile is fetched fresh
    user = get_object_or_404(User.objects.select_related('profile'), id=user_id)
    
    if request.method == 'POST':
        # Handle user update logic here
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_active = 'is_active' in request.POST
        user.profile.brand_name = request.POST.get('brand_name') if request.POST.get('brand_name') is not None else None
        # Update role if provided
        new_role = request.POST.get('role')
        if new_role in ['admin', 'staff', 'user']:
            user.profile.role = new_role
        
        # Update phone number if provided
        phone_number = request.POST.get('phone_number')
        if phone_number is not None:
            user.profile.phone_number = phone_number
        
        user.save()
        user.profile.save()
        
        messages.success(request, f'User "{user.username}" updated successfully!')
        return redirect('admin_interface:admin_users')
    else:
        # Prepare context for GET request
        context = {
            'user_obj': user,
            'title': f'Edit User: {user.username}'
        }
        return render(request, 'CustomAdmin/users/user_edit.html', context)

@login_required
def admin_user_delete(request, user_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    user = get_object_or_404(User, id=user_id)
    
    # Prevent deletion of superusers
    if user.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts.')
        return redirect('admin_interface:admin_users')
    
    # Prevent self-deletion
    if user == request.user:
        messages.error(request, 'Cannot delete your own account.')
        return redirect('admin_interface:admin_users')
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        messages.success(request, f'User "{username}" deleted successfully!')
        return redirect('admin_interface:admin_users')

    context = {
        'user_obj': user,
        'title': f'Delete User: {user.username}'
    }
    return render(request, 'CustomAdmin/users/user_delete.html', context)

@login_required
def admin_user_verify_email(request, user_id):
    """Mark a user's email as verified."""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.profile.email_verified = True
        user.profile.save()
        messages.success(request, f'Email for user "{user.username}" has been marked as verified.')
        return redirect('admin_interface:admin_user_edit', user_id=user.id)
    
    return redirect('admin_interface:admin_user_edit', user_id=user.id)


@login_required
def admin_user_unverify_email(request, user_id):
    """Mark a user's email as not verified."""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.profile.email_verified = False
        user.profile.save()
        messages.success(request, f'Email for user "{user.username}" has been marked as not verified.')
        return redirect('admin_interface:admin_user_edit', user_id=user.id)
    
    return redirect('admin_interface:admin_user_edit', user_id=user.id)


@login_required
def admin_user_send_verification(request, user_id):
    """Send email verification email to user."""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        from Accounts.utils import send_email_verification
        try:
            send_email_verification(user, request)
            messages.success(request, f'Verification email sent to {user.email}.')
        except Exception as e:
            messages.error(request, f'Failed to send verification email: {str(e)}')
        return redirect('admin_interface:admin_user_edit', user_id=user.id)
    
    return redirect('admin_interface:admin_user_edit', user_id=user.id)


@login_required
def admin_user_reset_password(request, user_id):
    """
    Admin-initiated password reset for users.
    
    Allows admin and staff users to reset any user's password.
    Includes proper validation and security measures.
    """
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    user = get_object_or_404(User, id=user_id)
    
    # Prevent admin from resetting their own password (optional security measure)
    # You can remove this check if you want admins to be able to reset their own passwords
    if user == request.user:
        messages.error(request, 'You cannot reset your own password from this interface. Please use the regular password change form.')
        return redirect('admin_interface:admin_users')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        # Validation
        if not password or not password_confirm:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'CustomAdmin/users/user_reset_password.html', {
                'user_obj': user,
                'title': f'Reset Password: {user.username}'
            })
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'CustomAdmin/users/user_reset_password.html', {
                'user_obj': user,
                'title': f'Reset Password: {user.username}'
            })
        
        # Password policy validation (you can customize this based on your requirements)
        if len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return render(request, 'CustomAdmin/users/user_reset_password.html', {
                'user_obj': user,
                'title': f'Reset Password: {user.username}'
            })
        
        # Reset the password
        user.set_password(password)
        user.save()
        
        # Log the action for audit purposes
        from Accounts.utils import log_user_activity
        log_user_activity(request.user, 'password_reset_by_admin', f'Reset password for user {user.username}', request)
        
        messages.success(request, f'Password for user "{user.username}" has been reset successfully!')
        return redirect('admin_interface:admin_users')
    
    context = {
        'user_obj': user,
        'title': f'Reset Password: {user.username}'
    }
    return render(request, 'CustomAdmin/users/user_reset_password.html', context)

@login_required
def admin_factories(request):
    profile = request.user.profile
    if profile.role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    f_country = request.GET.get('country')
    f_state = request.GET.get('state')
    f_city = request.GET.get('city')
    f_district = request.GET.get('distric')  # note spelling
    f_region = request.GET.get('region')
    f_category = request.GET.get('category')
    f_subcategory = request.GET.get('subcategory')
    f_search = request.GET.get('search', '')
    f_status = request.GET.get('status')
    f_deleted = request.GET.get('deleted', 'active')
    f_verified = request.GET.get('verified')   # ✅ NEW: 'verified', 'unverified', or None
    sort_by = request.GET.get('sort', '-created_at')  # ✅ NEW: default newest first

    # 2. Build Factory Queryset
    factories = Factory.objects.all_with_deleted().select_related(
        'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    )

    if f_country: factories = factories.filter(country_id=f_country)
    if f_state: factories = factories.filter(state_id=f_state)
    if f_city: factories = factories.filter(city_id=f_city)
    if f_district: factories = factories.filter(district_id=f_district)
    if f_region: factories = factories.filter(region_id=f_region)
    if f_category: factories = factories.filter(category_id=f_category)
    if f_subcategory: factories = factories.filter(subcategory_id=f_subcategory)
    
    # ✅ New: verified/unverified filter
    if f_verified == 'verified':
        factories = factories.filter(is_verified=True)
    elif f_verified == 'unverified':
        factories = factories.filter(is_verified=False)
    
    if f_search:
        terms = f_search.split()
        factories = and_search_filter(factories, terms, ['name'])
    
    if f_status == 'active':
        factories = factories.filter(is_active=True)
    elif f_status == 'inactive':
        factories = factories.filter(is_active=False)

    if f_deleted == 'deleted':
        factories = factories.filter(is_deleted=True)
    elif f_deleted == 'active':
        factories = factories.filter(is_deleted=False)

    # ✅ Apply sorting
    valid_sort_fields = ['name', 'created_at', 'updated_at', 'employee_count', 'annual_turnover']
    # Allow descending with '-'
    sort_key = sort_by
    if sort_key.startswith('-'):
        sort_field = sort_key[1:]
        if sort_field in valid_sort_fields:
            factories = factories.order_by(sort_key)
    else:
        if sort_by in valid_sort_fields:
            factories = factories.order_by(sort_by)
        else:
            factories = factories.order_by('-created_at')  # default

    # 3. CSV Export
    if 'download' in request.GET:
        return export_factories_to_csv(factories)

    # 4. PERSISTENT DROPDOWNS
    countries = Country.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    
    states = State.objects.filter(country_id=f_country, is_deleted=False) if f_country else State.objects.none()
    cities = City.objects.filter(state_id=f_state, is_deleted=False) if f_state else City.objects.none()
    districs = District.objects.filter(city_id=f_city, is_deleted=False) if f_city else District.objects.none()
    regions = Region.objects.filter(district_id=f_district, is_deleted=False) if f_district else Region.objects.none()
    subcategories = SubCategory.objects.filter(category_id=f_category, is_deleted=False) if f_category else SubCategory.objects.none()

    context = {
        'factories': factories,
        'countries': countries,
        'states': states,
        'cities': cities,
        'districs': districs,
        'regions': regions,
        'categories': categories,
        'subcategories': subcategories,
        'filters': {
            'country': f_country,
            'state': f_state,
            'city': f_city,
            'distric': f_district,
            'region': f_region,
            'category': f_category,
            'subcategory': f_subcategory,
            'search': f_search,
            'status': f_status,
            'deleted': f_deleted,
            'verified': f_verified,      # ✅ new
            'sort': sort_by,             # ✅ new
        }
    }
    return render(request, 'CustomAdmin/factories/factories.html', context)

@login_required
def admin_workers(request):
    profile = request.user.profile
    role = profile.role

    # RBAC Check
    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # ----- Capture all filter parameters -----
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    experience_min = request.GET.get('experience_min')
    experience_max = request.GET.get('experience_max')
    status = request.GET.get('status')
    gender = request.GET.get('gender')
    availability = request.GET.get('availability')
    country_id = request.GET.get('country')
    state_id = request.GET.get('state')
    city_id = request.GET.get('city')
    district_id = request.GET.get('district')
    region_id = request.GET.get('region')
    deleted_view = request.GET.get('deleted', 'active')
    search_query = request.GET.get('search', '')

    # ----- Base queryset (optimized) -----
    workers = Worker.objects.all().select_related(
        'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    )

    # ----- Soft delete handling -----
    if deleted_view == 'deleted':
        workers = Worker.objects.all_with_deleted().filter(is_deleted=True)
    elif deleted_view == 'all':
        workers = Worker.objects.all_with_deleted()
    else:
        workers = workers.filter(is_deleted=False)

    # ----- Apply filters -----
    if category_id:
        workers = workers.filter(category_id=category_id)
    if subcategory_id:
        workers = workers.filter(subcategory_id=subcategory_id)
    if country_id:
        workers = workers.filter(country_id=country_id)
    if state_id:
        workers = workers.filter(state_id=state_id)
    if city_id:
        workers = workers.filter(city_id=city_id)
    if district_id:
        workers = workers.filter(district_id=district_id)
    if region_id:
        workers = workers.filter(region_id=region_id)
    if gender:
        workers = workers.filter(gender=gender)
    if availability:
        workers = workers.filter(availability=availability)
    if experience_min:
        workers = workers.filter(years_of_experience__gte=experience_min)
    if experience_max:
        workers = workers.filter(years_of_experience__lte=experience_max)
    if status == 'active':
        workers = workers.filter(is_active=True)
    elif status == 'inactive':
        workers = workers.filter(is_active=False)

    # ----- Search -----
    if search_query:
        terms = search_query.split()
        workers = and_search_filter(
            workers,
            terms,
            ['full_name', 'email', 'phone_number', 'skills', 'category__name', 'subcategory__name']
        )

    # ----- CSV Export -----
    if 'download' in request.GET:
        return export_workers_to_csv(workers)

    # ----- Pagination (10 per page) -----
    paginator = Paginator(workers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # ----- Context data -----
    context = {
        'workers': page_obj,                     # paginated workers
        'categories': Category.objects.all(),
        'countries': Country.objects.all(),
        'gender_choices': Worker.GENDER_CHOICES,
        'availability_choices': Worker.AVAILABILITY_CHOICES,
        'filters': {
            'category': category_id,
            'subcategory': subcategory_id,
            'experience_min': experience_min,
            'experience_max': experience_max,
            'status': status,
            'gender': gender,
            'availability': availability,
            'country': country_id,
            'state': state_id,
            'city': city_id,
            'district': district_id,
            'region': region_id,
            'deleted': deleted_view,
        },
        'search_query': search_query,
    }
    return render(request, 'CustomAdmin/workers/workers.html', context)


@login_required
def admin_worker_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminWorkerForm(request.POST)
        if form.is_valid():
            worker = form.save(commit=False)
            worker.created_by = request.user   # <-- This is the key line
            worker.save()
            messages.success(request, f'Worker "{worker.full_name}" created successfully!')
            return redirect('admin_interface:admin_workers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminWorkerForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Worker'
    }
    return render(request, 'CustomAdmin/workers/worker_form.html', context)


@login_required
def admin_worker_edit(request, worker_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    worker = get_object_or_404(Worker, id=worker_id, is_deleted=False)

    if request.method == 'POST':
        form = AdminWorkerForm(request.POST, instance=worker)
        if form.is_valid():
            worker = form.save()
            messages.success(request, f'Worker "{worker.full_name}" updated successfully!')
            return redirect('admin_interface:admin_workers')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminWorkerForm(instance=worker)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Worker: {worker.full_name}',
        'worker': worker,
    }
    return render(request, 'CustomAdmin/workers/worker_form.html', context)

@login_required
def admin_worker_delete(request, worker_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    worker = get_object_or_404(Worker, id=worker_id, is_deleted=False)
    
    if request.method == 'POST':
        worker_name = worker.full_name
        worker.soft_delete()
        messages.success(request, f'Worker "{worker_name}" deleted successfully!')
        return redirect('admin_interface:admin_workers')

    context = {
        'worker': worker,
        'title': f'Delete Worker: {worker.full_name}'
    }
    return render(request, 'CustomAdmin/workers/worker_delete.html', context)

@login_required
def admin_worker_restore(request, worker_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    worker = get_object_or_404(Worker, id=worker_id)
    
    if request.method == 'POST':
        worker_name = worker.full_name
        worker.restore()
        messages.success(request, f'Worker "{worker_name}" restored successfully!')
        return redirect('admin_interface:admin_workers')

    context = {
        'worker': worker,
        'title': f'Restore Worker: {worker.full_name}'
    }
    return render(request, 'CustomAdmin/workers/worker_restore.html', context)

@login_required
def admin_worker_hard_delete(request, worker_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    worker = get_object_or_404(Worker.objects.all_with_deleted(), id=worker_id)
    
    if request.method == 'POST':
        worker_name = worker.full_name
        worker.hard_delete()
        messages.success(request, f'Worker "{worker_name}" permanently deleted successfully!')
        return redirect('admin_interface:admin_workers')

    context = {
        'worker': worker,
        'title': f'Permanently Delete Worker: {worker.full_name}'
    }
    return render(request, 'CustomAdmin/workers/worker_permanent_delete.html', context)

@login_required
def admin_worker_detail(request, worker_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    worker = get_object_or_404(Worker, id=worker_id, is_deleted=False)
    experiences = worker.experiences.all()

    context = {
        'worker': worker,
        'experiences': experiences,
        'title': f'Worker Details: {worker.full_name}'
    }
    return render(request, 'CustomAdmin/workers/worker_detail.html', context)

@login_required
def admin_reports(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser) :
        return render(request, 'CustomAdmin/permission_denied.html')

    # Handle report generation
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        format = request.POST.get('format')

        if report_type == 'factory':
            return generate_factory_report(start_date, end_date, format)
        elif report_type == 'worker':
            return generate_worker_report(start_date, end_date, format)
        elif report_type == 'combined':
            return generate_combined_report(start_date, end_date, format)

    return render(request, 'CustomAdmin/system/reports.html')

@login_required
def admin_notifications(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # TODO: Implement notification system
    return render(request, 'CustomAdmin/system/notifications.html')

@login_required
def admin_profile(request):
    profile = request.user.profile
    return render(request, 'CustomAdmin/system/profile.html', {'profile': profile})

# Location Management Views
@login_required
def admin_locations(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # Calculate summary statistics
    countries_total = Country.objects.filter(is_deleted=False).count()
    states_total = State.objects.filter(is_deleted=False).count()
    cities_total = City.objects.filter(is_deleted=False).count()
    districts_total = District.objects.filter(is_deleted=False).count()
    regions_total = Region.objects.filter(is_deleted=False).count()

    return render(request, 'CustomAdmin/locations/locations.html', {
        'countries_total': countries_total,
        'states_total': states_total,
        'cities_total': cities_total,
        'districts_total': districts_total,
        'regions_total': regions_total,
    })

@login_required
def admin_countries(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    countries = Country.objects.filter(is_deleted=False)
    
    # Add pagination
    paginator = Paginator(countries, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'CustomAdmin/locations/countries.html', {
        'countries': page_obj,
        'page_obj': page_obj,
        'location_type': 'Country'
    })

@login_required
def admin_country_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminCountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(request, f'Country "{country.name}" created successfully!')
            return redirect('admin_interface:admin_countries')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCountryForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Country'
    }
    return render(request, 'CustomAdmin/locations/country_form.html', context)

@login_required
def admin_country_edit(request, country_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    country = get_object_or_404(Country, id=country_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminCountryForm(request.POST, instance=country)
        if form.is_valid():
            country = form.save()
            messages.success(request, f'Country "{country.name}" updated successfully!')
            return redirect('admin_interface:admin_countries')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCountryForm(instance=country)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Country: {country.name}',
        'country': country
    }
    return render(request, 'CustomAdmin/locations/country_form.html', context)

@login_required
def admin_country_delete(request, country_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    country = get_object_or_404(Country, id=country_id, is_deleted=False)
    
    if request.method == 'POST':
        country_name = country.name
        country.delete()
        messages.success(request, f'Country "{country_name}" deleted successfully!')
        return redirect('admin_interface:admin_countries')

    context = {
        'country': country,
        'title': f'Delete Country: {country.name}'
    }
    return render(request, 'CustomAdmin/locations/country_delete.html', context)

@login_required
def admin_country_restore(request, country_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    country = get_object_or_404(Country.objects.all_with_deleted(), id=country_id)
    
    if request.method == 'POST':
        country_name = country.name
        country.restore()
        messages.success(request, f'Country "{country_name}" restored successfully!')
        return redirect('admin_interface:admin_countries')

    context = {
        'country': country,
        'title': f'Restore Country: {country.name}'
    }
    return render(request, 'CustomAdmin/locations/country_restore.html', context)

@login_required
def admin_country_detail(request, country_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    country = get_object_or_404(Country, id=country_id, is_deleted=False)
    states = country.states.filter(is_deleted=False)
    cities = City.objects.filter(state__in=states, is_deleted=False)
    districts = District.objects.filter(city__in=cities, is_deleted=False)
    regions = Region.objects.filter(district__in=districts, is_deleted=False)

    context = {
        'country': country,
        'states': states,
        'cities': cities,
        'total_cities': cities.count(),
        'total_districts': districts.count(),
        'total_regions': regions.count(),
        'title': f'Country Details: {country.name}'
    }
    return render(request, 'CustomAdmin/locations/country_detail.html', context)

@login_required
def admin_states(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    states = State.objects.filter(is_deleted=False)
    
    # Add pagination
    paginator = Paginator(states, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'CustomAdmin/locations/states.html', {
        'states': page_obj,
        'page_obj': page_obj,
        'location_type': 'State'
    })

@login_required
def admin_state_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminStateForm(request.POST)
        if form.is_valid():
            state = form.save()
            messages.success(request, f'State "{state.name}" created successfully!')
            return redirect('admin_interface:admin_states')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminStateForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New State'
    }
    return render(request, 'CustomAdmin/locations/state_form.html', context)

@login_required
def admin_state_edit(request, state_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    state = get_object_or_404(State, id=state_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminStateForm(request.POST, instance=state)
        if form.is_valid():
            state = form.save()
            messages.success(request, f'State "{state.name}" updated successfully!')
            return redirect('admin_interface:admin_states')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminStateForm(instance=state)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit State: {state.name}',
        'state': state
    }
    return render(request, 'CustomAdmin/locations/state_form.html', context)

@login_required
def admin_state_delete(request, state_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    state = get_object_or_404(State, id=state_id, is_deleted=False)
    
    if request.method == 'POST':
        state_name = state.name
        state.delete()
        messages.success(request, f'State "{state_name}" deleted successfully!')
        return redirect('admin_interface:admin_states')

    context = {
        'state': state,
        'title': f'Delete State: {state.name}'
    }
    return render(request, 'CustomAdmin/locations/state_delete.html', context)

@login_required
def admin_state_restore(request, state_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    state = get_object_or_404(State.objects.all_with_deleted(), id=state_id)
    
    if request.method == 'POST':
        state_name = state.name
        state.restore()
        messages.success(request, f'State "{state_name}" restored successfully!')
        return redirect('admin_interface:admin_states')

    context = {
        'state': state,
        'title': f'Restore State: {state.name}'
    }
    return render(request, 'CustomAdmin/locations/state_restore.html', context)

@login_required
def admin_state_detail(request, state_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    state = get_object_or_404(State, id=state_id, is_deleted=False)
    cities = state.cities.filter(is_deleted=False)

    context = {
        'state': state,
        'cities': cities,
        'title': f'State Details: {state.name}'
    }
    return render(request, 'CustomAdmin/locations/state_detail.html', context)

@login_required
def admin_cities(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    cities = City.objects.filter(is_deleted=False)
    
    # Add pagination
    paginator = Paginator(cities, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'CustomAdmin/locations/cities.html', {
        'cities': page_obj,
        'page_obj': page_obj,
        'location_type': 'City'
    })

@login_required
def admin_city_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminCityForm(request.POST)
        if form.is_valid():
            city = form.save()
            messages.success(request, f'City "{city.name}" created successfully!')
            return redirect('admin_interface:admin_cities')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCityForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New City'
    }
    return render(request, 'CustomAdmin/locations/city_form.html', context)

@login_required
def admin_city_edit(request, city_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    city = get_object_or_404(City, id=city_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminCityForm(request.POST, request.FILES, instance=city)
        if form.is_valid():
            city = form.save()
            messages.success(request, f'City "{city.name}" updated successfully!')
            return redirect('admin_interface:admin_cities')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCityForm(instance=city)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit City: {city.name}',
        'city': city
    }
    return render(request, 'CustomAdmin/locations/city_form.html', context)

@login_required
def admin_city_delete(request, city_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    city = get_object_or_404(City, id=city_id, is_deleted=False)
    
    if request.method == 'POST':
        city_name = city.name
        city.delete()
        messages.success(request, f'City "{city_name}" deleted successfully!')
        return redirect('admin_interface:admin_cities')

    context = {
        'city': city,
        'title': f'Delete City: {city.name}'
    }
    return render(request, 'CustomAdmin/locations/city_delete.html', context)

@login_required
def admin_city_restore(request, city_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    city = get_object_or_404(City.objects.all_with_deleted(), id=city_id)
    
    if request.method == 'POST':
        city_name = city.name
        city.restore()
        messages.success(request, f'City "{city_name}" restored successfully!')
        return redirect('admin_interface:admin_cities')

    context = {
        'city': city,
        'title': f'Restore City: {city.name}'
    }
    return render(request, 'CustomAdmin/locations/city_restore.html', context)

@login_required
def admin_city_detail(request, city_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    city = get_object_or_404(City, id=city_id, is_deleted=False)
    districts = city.districts.filter(is_deleted=False)
    regions = Region.objects.filter(district__city=city, is_deleted=False)

    context = {
        'city': city,
        'districts': districts,
        'regions': regions,
        'title': f'City Details: {city.name}'
    }
    return render(request, 'CustomAdmin/locations/city_detail.html', context)

@login_required
def admin_districts(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    districts = District.objects.filter(is_deleted=False)
    
    # Add pagination
    paginator = Paginator(districts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'CustomAdmin/locations/districts.html', {
        'districts': page_obj,
        'page_obj': page_obj,
        'location_type': 'District'
    })

@login_required
def admin_district_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminDistrictForm(request.POST)
        if form.is_valid():
            district = form.save()
            messages.success(request, f'District "{district.name}" created successfully!')
            return redirect('admin_interface:admin_districts')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminDistrictForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New District'
    }
    return render(request, 'CustomAdmin/locations/district_form.html', context)

@login_required
def admin_district_edit(request, district_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    district = get_object_or_404(District, id=district_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminDistrictForm(request.POST, instance=district)
        if form.is_valid():
            district = form.save()
            messages.success(request, f'District "{district.name}" updated successfully!')
            return redirect('admin_interface:admin_districts')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminDistrictForm(instance=district)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit District: {district.name}',
        'district': district
    }
    return render(request, 'CustomAdmin/locations/district_form.html', context)

@login_required
def admin_district_delete(request, district_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    district = get_object_or_404(District, id=district_id, is_deleted=False)
    
    if request.method == 'POST':
        district_name = district.name
        district.delete()
        messages.success(request, f'District "{district_name}" deleted successfully!')
        return redirect('admin_interface:admin_districts')

    context = {
        'district': district,
        'title': f'Delete District: {district.name}'
    }
    return render(request, 'CustomAdmin/locations/district_delete.html', context)

@login_required
def admin_district_restore(request, district_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    district = get_object_or_404(District.objects.all_with_deleted(), id=district_id)
    
    if request.method == 'POST':
        district_name = district.name
        district.restore()
        messages.success(request, f'District "{district_name}" restored successfully!')
        return redirect('admin_interface:admin_districts')

    context = {
        'district': district,
        'title': f'Restore District: {district.name}'
    }
    return render(request, 'CustomAdmin/locations/district_restore.html', context)

@login_required
def admin_district_detail(request, district_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    district = get_object_or_404(District, id=district_id, is_deleted=False)
    regions = district.regions.filter(is_deleted=False)
    active_regions_count = regions.filter(is_active=True).count()
    inactive_regions_count = regions.filter(is_active=False).count()

    context = {
        'district': district,
        'regions': regions,
        'active_regions_count': active_regions_count,
        'inactive_regions_count': inactive_regions_count,
        'title': f'District Details: {district.name}'
    }
    return render(request, 'CustomAdmin/locations/district_detail.html', context)

@login_required
def admin_regions(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    regions = Region.objects.filter(is_deleted=False)
    
    # Add pagination
    paginator = Paginator(regions, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'CustomAdmin/locations/regions.html', {
        'regions': page_obj,
        'page_obj': page_obj,
        'location_type': 'Region'
    })

@login_required
def admin_region_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminRegionForm(request.POST)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region "{region.name}" created successfully!')
            return redirect('admin_interface:admin_regions')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminRegionForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Region'
    }
    return render(request, 'CustomAdmin/locations/region_form.html', context)

@login_required
def admin_region_edit(request, region_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    region = get_object_or_404(Region, id=region_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminRegionForm(request.POST, instance=region)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region "{region.name}" updated successfully!')
            return redirect('admin_interface:admin_regions')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminRegionForm(instance=region)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Region: {region.name}',
        'region': region
    }
    return render(request, 'CustomAdmin/locations/region_form.html', context)

@login_required
def admin_region_delete(request, region_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    region = get_object_or_404(Region, id=region_id, is_deleted=False)
    
    if request.method == 'POST':
        region_name = region.name
        region.delete()
        messages.success(request, f'Region "{region_name}" deleted successfully!')
        return redirect('admin_interface:admin_regions')

    context = {
        'region': region,
        'title': f'Delete Region: {region.name}'
    }
    return render(request, 'CustomAdmin/locations/region_delete.html', context)

@login_required
def admin_region_restore(request, region_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    region = get_object_or_404(Region.objects.all_with_deleted(), id=region_id)
    
    if request.method == 'POST':
        region_name = region.name
        region.restore()
        messages.success(request, f'Region "{region_name}" restored successfully!')
        return redirect('admin_interface:admin_regions')

    context = {
        'region': region,
        'title': f'Restore Region: {region.name}'
    }
    return render(request, 'CustomAdmin/locations/region_restore.html', context)

@login_required
def admin_region_detail(request, region_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    region = get_object_or_404(Region, id=region_id, is_deleted=False)

    context = {
        'region': region,
        'title': f'Region Details: {region.name}'
    }
    return render(request, 'CustomAdmin/locations/region_detail.html', context)

# Category Management Views
@login_required
def admin_categories(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    categories = Category.objects.filter(is_deleted=False)
    
    # Calculate summary statistics
    subcategories_total = sum(category.subcategories.count() for category in categories)
    factories_total = sum(category.factories.count() for category in categories)
    workers_total = sum(category.workers.count() for category in categories)
    
    if request.method == 'POST':
        # Handle edit category
        category_id = request.POST.get('category_id')
        if category_id:
            category = get_object_or_404(Category, id=category_id, is_deleted=False)
            category.name = request.POST.get('name', category.name)
            category.description = request.POST.get('description', category.description)
            category.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('admin_interface:admin_categories')
        
        # Handle add category
        form = AdminCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_interface:admin_categories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCategoryForm()

    # Handle delete category
    delete_category_id = request.GET.get('delete_category')
    if delete_category_id:
        category = get_object_or_404(Category, id=delete_category_id, is_deleted=False)
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('admin_interface:admin_categories')

    # Add pagination
    paginator = Paginator(categories, 15)  # Show 25 categories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'CustomAdmin/locations/categories.html', {
        'categories': page_obj,
        'page_obj': page_obj,
        'form': form,
        'category_type': 'Category',
        'subcategories_total': subcategories_total,
        'factories_total': factories_total,
        'workers_total': workers_total,
    })

@login_required
def admin_subcategories(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # Filter subcategories
    subcategories = SubCategory.objects.filter(is_deleted=False)
    
    # Apply category filter if provided
    category_filter = request.GET.get('category')
    if category_filter:
        subcategories = subcategories.filter(category_id=category_filter)
    
    # Apply search filter
    search_filter = request.GET.get('search')
    if search_filter:
        terms = search_filter.split()
        subcategories = and_search_filter(
            subcategories,
            terms,
            ['name', 'description']
        )
    
    # Calculate summary statistics
    categories = Category.objects.filter(is_deleted=False)
    factories_total = sum(subcategory.factories.count() for subcategory in subcategories)
    workers_total = sum(subcategory.workers.count() for subcategory in subcategories)
    
    if request.method == 'POST':
        # Handle edit subcategory
        subcategory_id = request.POST.get('subcategory_id')
        if subcategory_id:
            subcategory = get_object_or_404(SubCategory, id=subcategory_id, is_deleted=False)
            subcategory.name = request.POST.get('name', subcategory.name)
            subcategory.description = request.POST.get('description', subcategory.description)
            category_id = request.POST.get('category')
            if category_id:
                subcategory.category_id = category_id
            subcategory.save()
            messages.success(request, f'Subcategory "{subcategory.name}" updated successfully!')
            return redirect('admin_interface:admin_subcategories')
        
        # Handle add subcategory
        form = AdminSubCategoryForm(request.POST)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'Subcategory "{subcategory.name}" created successfully!')
            return redirect('admin_interface:admin_subcategories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminSubCategoryForm()

    # Handle delete subcategory
    delete_subcategory_id = request.GET.get('delete_subcategory')
    if delete_subcategory_id:
        subcategory = get_object_or_404(SubCategory, id=delete_subcategory_id, is_deleted=False)
        subcategory_name = subcategory.name
        subcategory.delete()
        messages.success(request, f'Subcategory "{subcategory_name}" deleted successfully!')
        return redirect('admin_interface:admin_subcategories')

    # Add pagination
    paginator = Paginator(subcategories, 15)  # Show 25 subcategories per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'CustomAdmin/locations/subcategories.html', {
        'subcategories': page_obj,
        'page_obj': page_obj,
        'form': form,
        'category_type': 'Subcategory',
        'categories': categories,
        'factories_total': factories_total,
        'workers_total': workers_total,
    })

@login_required
def admin_category_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminCategoryForm(request.POST, request.FILES)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_interface:admin_categories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCategoryForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Category'
    }
    return render(request, 'CustomAdmin/locations/category_form.html', context)

@login_required
def admin_category_edit(request, category_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    category = get_object_or_404(Category, id=category_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminCategoryForm(request.POST, request.FILES, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('admin_interface:admin_categories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminCategoryForm(instance=category)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Category: {category.name}',
        'category': category
    }
    return render(request, 'CustomAdmin/locations/category_form.html', context)

@login_required
def admin_category_delete(request, category_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    category = get_object_or_404(Category, id=category_id, is_deleted=False)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('admin_interface:admin_categories')

    context = {
        'category': category,
        'title': f'Delete Category: {category.name}'
    }
    return render(request, 'CustomAdmin/locations/category_delete.html', context)

@login_required
def admin_category_restore(request, category_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    category = get_object_or_404(Category.objects.all_with_deleted(), id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.restore()
        messages.success(request, f'Category "{category_name}" restored successfully!')
        return redirect('admin_interface:admin_categories')

    context = {
        'category': category,
        'title': f'Restore Category: {category.name}'
    }
    return render(request, 'CustomAdmin/locations/category_restore.html', context)

@login_required
def admin_category_detail(request, category_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    category = get_object_or_404(Category, id=category_id, is_deleted=False)
    subcategories = category.subcategories.filter(is_deleted=False)
    factories = category.factories.filter(is_deleted=False)
    workers = category.workers.filter(is_deleted=False)

    context = {
        'category': category,
        'subcategories': subcategories,
        'factories': factories,
        'workers': workers,
        'title': f'Category Details: {category.name}'
    }
    return render(request, 'CustomAdmin/locations/category_detail.html', context)

@login_required
def admin_subcategory_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminSubCategoryForm(request.POST)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'Subcategory "{subcategory.name}" created successfully!')
            return redirect('admin_interface:admin_subcategories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminSubCategoryForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Subcategory'
    }
    return render(request, 'CustomAdmin/locations/subcategory_form.html', context)

@login_required
def admin_subcategory_edit(request, subcategory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    subcategory = get_object_or_404(SubCategory, id=subcategory_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminSubCategoryForm(request.POST, instance=subcategory)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'Subcategory "{subcategory.name}" updated successfully!')
            return redirect('admin_interface:admin_subcategories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminSubCategoryForm(instance=subcategory)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Subcategory: {subcategory.name}',
        'subcategory': subcategory
    }
    return render(request, 'CustomAdmin/locations/subcategory_form.html', context)

@login_required
def admin_subcategory_delete(request, subcategory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    subcategory = get_object_or_404(SubCategory, id=subcategory_id, is_deleted=False)
    
    if request.method == 'POST':
        subcategory_name = subcategory.name
        subcategory.delete()
        messages.success(request, f'Subcategory "{subcategory_name}" deleted successfully!')
        return redirect('admin_interface:admin_subcategories')

    context = {
        'subcategory': subcategory,
        'title': f'Delete Subcategory: {subcategory.name}'
    }
    return render(request, 'CustomAdmin/locations/subcategory_delete.html', context)

@login_required
def admin_subcategory_restore(request, subcategory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    subcategory = get_object_or_404(SubCategory.objects.all_with_deleted(), id=subcategory_id)
    
    if request.method == 'POST':
        subcategory_name = subcategory.name
        subcategory.restore()
        messages.success(request, f'Subcategory "{subcategory_name}" restored successfully!')
        return redirect('admin_interface:admin_subcategories')

    context = {
        'subcategory': subcategory,
        'title': f'Restore Subcategory: {subcategory.name}'
    }
    return render(request, 'CustomAdmin/locations/subcategory_restore.html', context)

@login_required
def admin_subcategory_detail(request, subcategory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    subcategory = get_object_or_404(SubCategory, id=subcategory_id, is_deleted=False)
    factories = subcategory.factories.filter(is_deleted=False)
    workers = subcategory.workers.filter(is_deleted=False)

    context = {
        'subcategory': subcategory,
        'factories': factories,
        'workers': workers,
        'title': f'Subcategory Details: {subcategory.name}'
    }
    return render(request, 'CustomAdmin/locations/subcategory_detail.html', context)

def export_factories_to_csv(factories):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="factories.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Factory Name','Contact Person','Contact', 'Category', 'Sub Category', 'Location', 'Capacity', 'Owner', 'Status'])

    for factory in factories:
        owner = ', '.join([profile.user.username for profile in factory.profiles.all()]) if factory.profiles.exists() else 'No owner'
        location = f"{factory.city.name}, {factory.state.name}, {factory.country.name}"
        writer.writerow([
            factory.id,
            factory.name,
            factory.contact_person,
            factory.contact_phone,
            factory.category.name,
            factory.subcategory.name if factory.subcategory else 'N/A',
            location,
            owner,
            'Active' if factory.is_active else 'Inactive',
        ])

    return response

def export_workers_to_csv(workers):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="workers.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name','Phone No.', 'Category', 'Position', 'Factory', 'Experience', 'Age', 'Gender', 'Status'])

    for worker in workers:
        
        age = None
        if worker.date_of_birth:
            from datetime import date
            today = date.today()
            age = today.year - worker.date_of_birth.year - ((today.month, today.day) < (worker.date_of_birth.month, worker.date_of_birth.day))
        writer.writerow([
            worker.id,
            worker.full_name,
            worker.phone_number,
            worker.category,
     
         
            f"{worker.years_of_experience} years",
            f"{age} years" if age else 'N/A',
            worker.gender,
            'Active' if worker.is_active else 'Inactive',
        ])

    return response

def generate_factory_report(start_date, end_date, format):
    # Implement factory report generation
    factories = Factory.objects.filter(created_at__range=[start_date, end_date])

    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="factory_report_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Category', 'Sub Category', 'Location', 'Phone Number', 'Owner', 'Created At'])

        for factory in factories:
            owner = ', '.join([profile.user.username for profile in factory.profiles.all()]) if factory.profiles.exists() else 'No owner'
            location = f"{factory.city.name}, {factory.state.name}, {factory.country.name}"
            writer.writerow([
                factory.id,
                factory.name,
                factory.category.name,
                factory.subcategory.name if factory.subcategory else 'N/A',
                location,
                factory.contact_phone,
                owner,
                factory.created_at,
            ])

        return response
    elif format == 'excel':
        # Implement Excel export
        pass
    elif format == 'pdf':
        # Implement PDF export
        pass

def generate_worker_report(start_date, end_date, format):
    # Implement worker report generation
    workers = Worker.objects.filter(created_at__range=[start_date, end_date])

    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="worker_report_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['ID', 'Name', 'Category', 'Contact Info', 'Factory', 'Experience', 'Age', 'Gender', 'Created At'])

        for worker in workers:
     
            age = None
            if worker.date_of_birth:
                from datetime import date
                today = date.today()
                age = today.year - worker.date_of_birth.year - ((today.month, today.day) < (worker.date_of_birth.month, worker.date_of_birth.day))
            writer.writerow([
                worker.id,
                worker.full_name,
                worker.category,
                worker.phone_number,
                f"{worker.years_of_experience} years",
                f"{age} years" if age else 'N/A',
                worker.gender,
                worker.created_at,
            ])

        return response
    elif format == 'excel':
        # Implement Excel export
        pass
    elif format == 'pdf':
        # Implement PDF export
        pass

def generate_combined_report(start_date, end_date, format):
    # Implement combined report generation
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="combined_report_{start_date}_to_{end_date}.csv"'

        writer = csv.writer(response)
        writer.writerow(['Type', 'ID', 'Name','Phone No.', 'Category', 'Details', 'Created At'])

        factories = Factory.objects.filter(created_at__range=[start_date, end_date])
        workers = Worker.objects.filter(created_at__range=[start_date, end_date])

        for factory in factories:
            location = f"{factory.city.name}, {factory.state.name}, {factory.country.name}"
            writer.writerow([
                'Factory',
                factory.id,
                factory.name,
                factory.contact_phone,
                factory.category.name,
                location,
                factory.created_at,
            ])

        for worker in workers:
            writer.writerow([
                'Worker',
                worker.id,
                worker.full_name,
                worker.phone_number,
                worker.category,
                f"{worker.position}",
                worker.created_at,
            ])

        return response
    elif format == 'excel':
        # Implement Excel export
        pass
    elif format == 'pdf':
        # Implement PDF export
        pass

# Factory CRUD Views
@login_required
def admin_factory_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminFactoryForm(request.POST, request.FILES)
        if form.is_valid():
            factory = form.save()
            
            # Handle multiple image uploads
            image_files = request.FILES.getlist('image')
            if image_files:
                from Karkahan.models import FactoryImage
                import os
                
                for idx, image_file in enumerate(image_files):
                    # Validate image file
                    # Check file size (max 5MB)
                    if image_file.size > 5 * 1024 * 1024:
                        messages.error(request, f'Image "{image_file.name}" is too large. Max size is 5MB.')
                        continue
                    
                    # Check file extension
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                    file_extension = os.path.splitext(image_file.name)[1].lower()
                    if file_extension not in valid_extensions:
                        messages.error(request, f'Invalid format for "{image_file.name}". Please upload JPG, PNG, GIF, or WebP files.')
                        continue
                    
                    # Create a FactoryImage record for the uploaded image
                    new_image = FactoryImage.objects.create(
                        factory=factory,
                        image=image_file,
                        alt_text=f"Image uploaded via admin form - {factory.name}"
                    )
                    
                    # Set as primary if no primary image exists
                    if not factory.images.filter(is_primary=True).exists():
                        new_image.is_primary = True
                        new_image.save()
            
            messages.success(request, f'Factory "{factory.name}" created successfully!')
            return redirect('admin_interface:admin_factories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminFactoryForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Factory'
    }
    return render(request, 'CustomAdmin/factories/factory_form.html', context)

@login_required
def admin_factory_edit(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    factory = get_object_or_404(Factory, id=factory_id)
    
    # Add view statistics to context
    try:
        view_stats = factory.view_stats
    except:
        # Create stats if they don't exist
        from Karkahan.models import FactoryViewStats
        view_stats = FactoryViewStats.objects.create(factory=factory)
    
    if request.method == 'POST':
        # Handle featured image removal
        if 'remove_featured_image' in request.POST:
            if factory.featured_image:
                factory.featured_image = None
                factory.save()
                messages.success(request, f'Featured image removed successfully from factory "{factory.name}"!')
                return redirect('admin_interface:admin_factory_edit', factory_id=factory.id)
        
        # Handle FactoryImage removal
        if 'remove_factory_image' in request.POST:
            image_id = request.POST.get('image_id')
            if image_id:
                try:
                    factory_image = factory.images.get(id=image_id)
                    factory_image.delete()
                    messages.success(request, f'Image removed successfully from factory "{factory.name}"!')
                except:
                    messages.error(request, 'Image not found.')
                return redirect('admin_interface:admin_factory_edit', factory_id=factory.id)
        
        # Handle setting primary image
        if 'set_primary_image' in request.POST:
            image_id = request.POST.get('image_id')
            if image_id:
                try:
                    # Remove primary status from all images
                    factory.images.update(is_primary=False)
                    # Set new primary image
                    factory_image = factory.images.get(id=image_id)
                    factory_image.is_primary = True
                    factory_image.save()
                    messages.success(request, f'Primary image set successfully for factory "{factory.name}"!')
                except:
                    messages.error(request, 'Image not found.')
                return redirect('admin_interface:admin_factory_edit', factory_id=factory.id)
        
        form = AdminFactoryForm(request.POST, request.FILES, instance=factory)
        if form.is_valid():
            factory = form.save()
            
            # Handle multiple image uploads
            image_files = request.FILES.getlist('image')
            if image_files:
                from Karkahan.models import FactoryImage
                import os
                
                for image_file in image_files:
                    # Validate image file
                    # Check file size (max 5MB)
                    if image_file.size > 5 * 1024 * 1024:
                        messages.error(request, f'Image "{image_file.name}" is too large. Max size is 5MB.')
                        continue
                    
                    # Check file extension
                    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                    file_extension = os.path.splitext(image_file.name)[1].lower()
                    if file_extension not in valid_extensions:
                        messages.error(request, f'Invalid format for "{image_file.name}". Please upload JPG, PNG, GIF, or WebP files.')
                        continue
                    
                    # Create a FactoryImage record for the uploaded image
                    new_image = FactoryImage.objects.create(
                        factory=factory,
                        image=image_file,
                        alt_text=f"Image uploaded via admin form - {factory.name}"
                    )
                    
                    # Set as primary if no primary image exists
                    if not factory.images.filter(is_primary=True).exists():
                        new_image.is_primary = True
                        new_image.save()
                
                messages.success(request, f'{len(image_files)} image(s) uploaded successfully for factory "{factory.name}"!')
            
            messages.success(request, f'Factory "{factory.name}" updated successfully!')
            return redirect('admin_interface:admin_factories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminFactoryForm(instance=factory)

    # Get existing images for display
    factory_images = factory.images.all()

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Factory: {factory.name}',
        'factory': factory,
        'view_stats': view_stats,
        'factory_images': factory_images
    }
    return render(request, 'CustomAdmin/factories/factory_form.html', context)

@login_required
def admin_factory_delete(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    factory = get_object_or_404(Factory, id=factory_id)
    
    if request.method == 'POST':
        factory_name = factory.name
        factory.delete()
        messages.success(request, f'Factory "{factory_name}" deleted successfully!')
        return redirect('admin_interface:admin_factories')

    context = {
        'factory': factory,
        'title': f'Delete Factory: {factory.name}'
    }
    return render(request, 'CustomAdmin/factories/factory_delete.html', context)

@login_required
def admin_factory_restore(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    factory = get_object_or_404(Factory.objects.all_with_deleted(), id=factory_id)
    
    if request.method == 'POST':
        factory_name = factory.name
        factory.restore()
        messages.success(request, f'Factory "{factory_name}" restored successfully!')
        return redirect('admin_interface:admin_factories')

    context = {
        'factory': factory,
        'title': f'Restore Factory: {factory.name}'
    }
    return render(request, 'CustomAdmin/factories/factory_restore.html', context)

@login_required
def admin_factory_hard_delete(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    factory = get_object_or_404(Factory.objects.all_with_deleted(), id=factory_id)
    
    if request.method == 'POST':
        factory_name = factory.name
        factory.hard_delete()
        messages.success(request, f'Factory "{factory_name}" permanently deleted successfully!')
        return redirect('admin_interface:admin_factories')

    context = {
        'factory': factory,
        'title': f'Permanently Delete Factory: {factory.name}'
    }
    return render(request, 'CustomAdmin/factories/factory_permanent_delete.html', context)

@login_required
def admin_factory_detail(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    factory = get_object_or_404(Factory, id=factory_id)
    images = factory.images.all()
    
    # Add view statistics to context
    try:
        view_stats = factory.view_stats
    except:
        # Create stats if they don't exist
        from Karkahan.models import FactoryViewStats
        view_stats = FactoryViewStats.objects.create(factory=factory)

    context = {
        'factory': factory,
        'images': images,
        'view_stats': view_stats,
        'title': f'Factory Details: {factory.name}'
    }
    return render(request, 'CustomAdmin/factories/factory_detail.html', context)

@login_required
def admin_factory_copy(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    original = get_object_or_404(Factory, id=factory_id)

    # Create a copy by resetting primary key and unique fields
    factory_copy = Factory(
        name=f"Copy of {original.name}",
        slug=None,                     # will be auto‑generated on save
        factory_code=None,             # will be auto‑generated
        description=original.description,
        category=original.category,
        subcategory=original.subcategory,
        country=original.country,
        state=original.state,
        city=original.city,
        district=original.district,
        region=original.region,
        address=original.address,
        pincode=original.pincode,
        contact_person=original.contact_person,
        contact_phone=original.contact_phone,
        contact_email=original.contact_email,
        website=original.website,
        established_year=original.established_year,
        employee_count=original.employee_count,
        annual_turnover=original.annual_turnover,
        price=original.price,
        factory_type=original.factory_type,
        production_capacity=original.production_capacity,
        working_hours=original.working_hours,
        holidays=original.holidays,
        features=original.features,
        is_active=original.is_active,
        is_verified=original.is_verified,
        created_by=request.user,
        video_url=original.video_url,
    )
    factory_copy.save()

    # Copy images (the same files, not new uploads)
    for img in original.images.all():
        FactoryImage.objects.create(
            factory=factory_copy,
            image=img.image,          # same file reference
            alt_text=img.alt_text,
            is_primary=img.is_primary
        )

    messages.success(request, f'Factory "{original.name}" duplicated. You can now edit the copy.')
    return redirect('admin_interface:admin_factory_edit', factory_id=factory_copy.id)

# Blog CRUD Views
@login_required
def admin_blogs(request):
    profile = request.user.profile
    if profile.role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    f_category = request.GET.get('category')
    f_subcategory = request.GET.get('subcategory')
    f_author = request.GET.get('author')
    f_status = request.GET.get('status')
    f_country = request.GET.get('country')
    f_state = request.GET.get('state')
    f_city = request.GET.get('city')
    f_district = request.GET.get('district')
    f_region = request.GET.get('region')
    f_deleted = request.GET.get('deleted', 'active')  # 'active', 'deleted', 'all'
    f_search = request.GET.get('search', '')  # Search from navbar

    # 2. Build Queryset
    blogs = BlogPost.objects.all_with_deleted().select_related(
        'author', 'category', 'subcategory', 'country', 'state', 'city'
    )

    if f_category: blogs = blogs.filter(category_id=f_category)
    if f_subcategory: blogs = blogs.filter(subcategory_id=f_subcategory)
    if f_author: blogs = blogs.filter(author_id=f_author)
    if f_country: blogs = blogs.filter(country_id=f_country)
    if f_state: blogs = blogs.filter(state_id=f_state)
    if f_city: blogs = blogs.filter(city_id=f_city)
    if f_district: blogs = blogs.filter(district_id=f_district)
    if f_region: blogs = blogs.filter(region_id=f_region)
    
    if f_status == 'published':
        blogs = blogs.filter(is_published=True)
    elif f_status == 'draft':
        blogs = blogs.filter(is_published=False)

    # Filter by deleted status
    if f_deleted == 'deleted':
        blogs = blogs.filter(is_deleted=True)
    elif f_deleted == 'active':
        blogs = blogs.filter(is_deleted=False)

    # Apply search filter
    if f_search:
        terms = f_search.split()
        blogs = and_search_filter(
            blogs,
            terms,
            ['title', 'excerpt', 'content', 'author__username', 'category__name']
        )

    # 3. Persistent Dropdowns (Fetch options based on current selections)
    countries = Country.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    authors = User.objects.filter(blog_posts__isnull=False).distinct()
    
    # Cascading Data
    states = State.objects.filter(country_id=f_country, is_deleted=False) if f_country else State.objects.none()
    cities = City.objects.filter(state_id=f_state, is_deleted=False) if f_state else City.objects.none()
    districs = District.objects.filter(city_id=f_city, is_deleted=False) if f_city else District.objects.none()
    regions = Region.objects.filter(district_id=f_district, is_deleted=False) if f_district else Region.objects.none()
    subcategories = SubCategory.objects.filter(category_id=f_category, is_deleted=False) if f_category else SubCategory.objects.none()

    context = {
        'blogs': blogs,
        'countries': countries,
        'states': states,
        'cities': cities,
        'districs': districs,
        'regions': regions,
        'categories': categories,
        'subcategories': subcategories,
        'authors': authors,
        'filters': {
            'category': f_category,
            'subcategory': f_subcategory,
            'author': f_author,
            'status': f_status,
            'country': f_country,
            'state': f_state,
            'city': f_city,
            'district': f_district,
            'region': f_region,
            'deleted': f_deleted,
            'search': f_search,
        }
    }
    return render(request, 'CustomAdmin/blogs/blogs.html', context)

@login_required
def admin_blog_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminBlogForm(request.POST, request.FILES)
        if form.is_valid():
            blog = form.save()
            messages.success(request, f'Blog post "{blog.title}" created successfully!')
            return redirect('admin_interface:admin_blogs')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminBlogForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Blog Post'
    }
    return render(request, 'CustomAdmin/blogs/blog_form.html', context)

@login_required
def admin_blog_edit(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost, id=blog_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminBlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            blog = form.save()
            messages.success(request, f'Blog post "{blog.title}" updated successfully!')
            return redirect('admin_interface:admin_blogs')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminBlogForm(instance=blog)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Blog Post: {blog.title}',
        'blog': blog
    }
    return render(request, 'CustomAdmin/blogs/blog_form.html', context)

@login_required
def admin_blog_delete(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost, id=blog_id, is_deleted=False)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.delete()
        messages.success(request, f'Blog post "{blog_title}" deleted successfully!')
        return redirect('admin_interface:admin_blogs')

    context = {
        'blog': blog,
        'title': f'Delete Blog Post: {blog.title}'
    }
    return render(request, 'CustomAdmin/blogs/blog_delete.html', context)

@login_required
def admin_blog_restore(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost.objects.all_with_deleted(), id=blog_id)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.restore()
        messages.success(request, f'Blog post "{blog_title}" restored successfully!')
        return redirect('admin_interface:admin_blogs')

    context = {
        'blog': blog,
        'title': f'Restore Blog Post: {blog.title}'
    }
    return render(request, 'CustomAdmin/blogs/blog_restore.html', context)

@login_required
def admin_blog_detail(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost, id=blog_id, is_deleted=False)
    images = blog.images.all()

    context = {
        'blog': blog,
        'images': images,
        'title': f'Blog Post Details: {blog.title}'
    }
    return render(request, 'CustomAdmin/blogs/blog_detail.html', context)

@login_required
def admin_blog_soft_delete(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost, id=blog_id, is_deleted=False)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.delete()
        messages.success(request, f'Blog post "{blog_title}" soft deleted successfully!')
        return redirect('admin_interface:admin_blogs')

    context = {
        'blog': blog,
        'title': f'Soft Delete Blog Post: {blog.title}'
    }
    return render(request, 'admin_interface/blogs/blog_soft_delete.html', context)

@login_required
def admin_blog_hard_delete(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost.objects.all_with_deleted(), id=blog_id)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.hard_delete()
        messages.success(request, f'Blog post "{blog_title}" permanently deleted successfully!')
        return redirect('admin_interface:admin_blogs')

    context = {
        'blog': blog,
        'title': f'Permanently Delete Blog Post: {blog.title}'
    }
    return render(request, 'admin_interface/blogs/blog_hard_delete.html', context)

@login_required
def admin_blog_permanent_delete(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost.objects.all_with_deleted(), id=blog_id)
    
    if request.method == 'POST':
        blog_title = blog.title
        blog.hard_delete()
        messages.success(request, f'Blog post "{blog_title}" permanently deleted successfully!')
        return redirect('admin_interface:admin_blogs')

    context = {
        'blog': blog,
        'title': f'Permanently Delete Blog Post: {blog.title}'
    }
    return render(request, 'admin_interface/blogs/blog_permanent_delete.html', context)

@login_required
def admin_blog_images(request, blog_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    blog = get_object_or_404(BlogPost, id=blog_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminBlogImageForm(request.POST, request.FILES)
        if form.is_valid():
            blog_image = form.save(commit=False)
            blog_image.blog_post = blog
            blog_image.save()
            messages.success(request, 'Blog image added successfully!')
            return redirect('admin_interface:admin_blog_images', blog_id=blog_id)
    else:
        form = AdminBlogImageForm()

    images = blog.images.all()

    context = {
        'blog': blog,
        'form': form,
        'images': images,
        'title': f'Manage Images: {blog.title}'
    }
    return render(request, 'CustomAdmin/blogs/blog_images.html', context)


@login_required
def admin_faq_list(request):
    profile = request.user.profile
    role = profile.role
    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')
    
    questions = FAQQuestion.objects.all().select_related('category', 'created_by')
    
    # Filtering
    category = request.GET.get('category')
    status = request.GET.get('status')
    if category:
        questions = questions.filter(category_id=category)
    if status:
        questions = questions.filter(status=status)
    
    # Search
    search_query = request.GET.get('search', '') or request.GET.get('q', '')
    if search_query:
        terms = search_query.split()
        questions = and_search_filter(
            questions,
            terms,
            ['title', 'question_text', 'answer_text']
        )
    
    # Pagination
    paginator = Paginator(questions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'status_choices': FAQQuestion.STATUS_CHOICES,
        'search_query': search_query,
        'selected_category': category,
        'selected_status': status,
    }
    return render(request, 'CustomAdmin/faq/faq_list.html', context)


@login_required
def admin_faq_create(request):
    profile = request.user.profile
    role = profile.role
    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')
    
    if request.method == 'POST':
        form = AdminFAQQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.created_by = request.user
            # Sync is_published with status
            question.is_published = (question.status == 'published')
            question.is_deleted = False
            if question.is_published and not question.published_at:
                question.published_at = timezone.now()
            question.save()
            messages.success(request, f'FAQ "{question.title}" created successfully.')
            return redirect('admin_interface:admin_faq')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminFAQQuestionForm()
    
    context = {
        'form': form,
        'title': 'Create FAQ Question'
    }
    return render(request, 'CustomAdmin/faq/faq_form.html', context)


@login_required
def admin_faq_edit(request, pk):
    profile = request.user.profile
    role = profile.role
    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')
    
    question = get_object_or_404(FAQQuestion, pk=pk)
    
    if request.method == 'POST':
        form = AdminFAQQuestionForm(request.POST, instance=question)
        if form.is_valid():
            q = form.save(commit=False)
            q.updated_by = request.user
            # Sync is_published with status
            q.is_published = (q.status == 'published')
            if q.is_published and not q.published_at:
                q.published_at = timezone.now()
            q.save()
            messages.success(request, f'FAQ "{q.title}" updated successfully.')
            return redirect('admin_interface:admin_faq')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = AdminFAQQuestionForm(instance=question)
    
    context = {
        'form': form,
        'title': 'Edit FAQ Question',
        'question': question,
    }
    return render(request, 'CustomAdmin/faq/faq_form.html', context)


@login_required
def admin_faq_delete(request, pk):
    profile = request.user.profile
    role = profile.role
    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')
    
    question = get_object_or_404(FAQQuestion, pk=pk)
    
    if request.method == 'POST':
        question.is_deleted = True
        question.save()
        messages.success(request, f'FAQ "{question.title}" moved to trash.')
        return redirect('admin_interface:admin_faq')
    
    # GET request – show confirmation page
    context = {
        'question': question,
        'title': 'Delete FAQ Question',
    }
    return render(request, 'CustomAdmin/faq/faq_confirm_delete.html', context)



def admin_contacts(request, type=None):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # --- Valid types (must match ContactMessage.INQUIRY_TYPES keys) ---
    valid_types = ['enquiry', 'export', 'karigar', 'online_class']
    if type and type not in valid_types:
        type = None  # fallback to all

    # --- Capture filter parameters from GET ---
    search = request.GET.get('search', '')
    status = request.GET.get('status')          # 'read' / 'unread'
    user_id = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    deleted_view = request.GET.get('deleted', 'active')
    type_filter = request.GET.get('type_filter', type)  # allow overriding via GET

    # Determine effective type filter: URL type > GET parameter > None
    effective_type = type_filter if type_filter in valid_types else type

    # --- Build queryset ---
    messages = ContactMessage.objects.all_with_deleted().select_related('user')

    # Apply type filter
    if effective_type:
        messages = messages.filter(type=effective_type)

    # Apply search (AND across name, email, subject, message)
    if search:
        terms = search.split()
        messages = and_search_filter(messages, terms, ['name', 'email', 'subject', 'message'])

    # Read/unread status
    if status == 'unread':
        messages = messages.filter(is_read=False)
    elif status == 'read':
        messages = messages.filter(is_read=True)

    # User filter
    if user_id:
        messages = messages.filter(user_id=user_id)

    # Date range
    if start_date:
        messages = messages.filter(created_at__date__gte=start_date)
    if end_date:
        messages = messages.filter(created_at__date__lte=end_date)

    # Deleted status
    if deleted_view == 'deleted':
        messages = messages.filter(is_deleted=True)
    elif deleted_view == 'active':
        messages = messages.filter(is_deleted=False)

    # --- Summary statistics (respecting current filters, but optionally we may want totals without type) ---
    # For dashboard counts, we'll show overall numbers (all types) – but you can change to filtered.
    # Here we keep overall counts for the sidebar.
    total_all = ContactMessage.objects.filter(is_deleted=False).count()
    unread_all = ContactMessage.objects.filter(is_read=False, is_deleted=False).count()
    read_all = ContactMessage.objects.filter(is_read=True, is_deleted=False).count()
    first_day_of_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_all = ContactMessage.objects.filter(created_at__gte=first_day_of_month, is_deleted=False).count()

    # --- CSV export (respects current filters) ---
    if 'download' in request.GET:
        return export_contact_messages_to_csv(messages, type_label=effective_type)

    # --- Pagination (20 per page) ---
    paginator = Paginator(messages, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # --- Get distinct users for filter dropdown (respect type filter optionally) ---
    users_qs = User.objects.filter(contactmessage__isnull=False)
    if effective_type:
        users_qs = users_qs.filter(contactmessage__type=effective_type)
    users = users_qs.distinct()

    # --- Prepare context ---
    context = {
        'Messages': page_obj,
        'users': users,
        'unread_count': unread_all,
        'read_count': read_all,
        'this_month_count': this_month_all,
        'total_count': total_all,
        'current_type': effective_type,   # for highlighting in template
        'type_choices': dict(ContactMessage.INQUIRY_TYPES),  # display mapping
        'filters': {
            'search': search,
            'status': status,
            'user': user_id,
            'start_date': start_date,
            'end_date': end_date,
            'deleted': deleted_view,
            'type_filter': effective_type,
        },
    }
    return render(request, 'CustomAdmin/contacts/contacts.html', context)

@login_required
def mark_message_read(request, message_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        message.mark_as_read()
        messages.success(request, f'Message from {message.name} marked as read.')
        return redirect('admin_interface:admin_contacts')

    context = {
        'message': message,
        'title': f'Mark as Read: {message.subject}'
    }
    return render(request, 'CustomAdmin/contacts/mark_read.html', context)

@login_required
def delete_message(request, message_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        try:
            message_name = message.name
            message.delete()
            return JsonResponse({
                'success': True,
                'message': f'Message from {message_name} deleted successfully.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # For GET requests, return the delete confirmation page
    context = {
        'message': message,
        'title': f'Delete Message: {message.subject}'
    }
    return render(request, 'CustomAdmin/contacts/delete_message.html', context)

@login_required
def bulk_actions(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.get('selected_ids', '').split(',')
        
        if not selected_ids or selected_ids == ['']:
            messages.error(request, 'Please select at least one message.')
            return redirect('admin_interface:admin_contacts')

        contact_messages = ContactMessage.objects.filter(id__in=selected_ids)
        
        if action == 'mark-read':
            count = 0
            for message in contact_messages:
                if not message.is_read:
                    message.mark_as_read()
                    count += 1
            messages.success(request, f'Marked {count} messages as read.')
        
        elif action == 'mark-unread':
            count = 0
            for message in contact_messages:
                if message.is_read:
                    message.is_read = False
                    message.read_at = None
                    message.save()
                    count += 1
            messages.success(request, f'Marked {count} messages as unread.')
        
        elif action == 'delete':
            count = contact_messages.count()
            for message in contact_messages:
                message.delete()
            messages.success(request, f'Deleted {count} messages.')
        
        else:
            messages.error(request, 'Invalid action.')
    
    return redirect('admin_interface:admin_contacts')

def export_contact_messages_to_csv(messages, type_label=None):
    response = HttpResponse(content_type='text/csv')
    filename = f"contact_messages_{type_label or 'all'}_{timezone.now().strftime('%Y%m%d')}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Type', 'Name', 'Phone No.', 'Email', 'Subject', 'Message', 'User', 'Status', 'Created At', 'Read At'])

    for message in messages:
        writer.writerow([
            message.id,
            message.get_type_display(),
            message.name,
            message.mobile_number,
            message.email,
            message.subject,
            message.message.replace('\n', ' ').replace('\r', ''),
            message.user.username if message.user else 'Guest',
            'Read' if message.is_read else 'Unread',
            message.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            message.read_at.strftime('%Y-%m-%d %H:%M:%S') if message.read_at else '',
        ])

    return response

# Home Page Videos Views
@login_required
def admin_homepage_videos(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    f_status = request.GET.get('status')
    f_search = request.GET.get('search', '')
    f_deleted = request.GET.get('deleted', 'active')  # 'active', 'deleted', 'all'

    # 2. Build Queryset
    videos = HomePageVideo.objects.all_with_deleted().select_related()

    if f_search: videos = videos.filter(title__icontains=f_search)
    
    if f_status == 'active':
        videos = videos.filter(is_active=True)
    elif f_status == 'inactive':
        videos = videos.filter(is_active=False)

    # Filter by deleted status
    if f_deleted == 'deleted':
        videos = videos.filter(is_deleted=True)
    elif f_deleted == 'active':
        videos = videos.filter(is_deleted=False)

    # 3. CSV Export
    if 'download' in request.GET:
        return export_homepage_videos_to_csv(videos)

    # 4. Calculate Summary Statistics
    total_count = videos.count()
    active_count = videos.filter(is_active=True).count()
    inactive_count = videos.filter(is_active=False).count()
    deleted_count = videos.filter(is_deleted=True).count()

    context = {
        'videos': videos,
        'total_count': total_count,
        'active_count': active_count,
        'inactive_count': inactive_count,
        'deleted_count': deleted_count,
        'filters': {
            'status': f_status,
            'search': f_search,
            'deleted': f_deleted,
        }
    }
    return render(request, 'CustomAdmin/videos/videos.html', context)

@login_required
def admin_homepage_video_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminHomePageVideoForm(request.POST, request.FILES)
        if form.is_valid():
            video = form.save()
            
            # Handle constraint: if this video is active, deactivate others
            if video.is_active:
                HomePageVideo.objects.filter(is_active=True).exclude(id=video.id).update(is_active=False)
            
            messages.success(request, f'Home page video "{video.title}" created successfully!')
            return redirect('admin_interface:admin_homepage_videos')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminHomePageVideoForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Home Page Video'
    }
    return render(request, 'CustomAdmin/videos/video_form.html', context)

@login_required
def admin_homepage_video_edit(request, video_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    video = get_object_or_404(HomePageVideo, id=video_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminHomePageVideoForm(request.POST, request.FILES, instance=video)
        if form.is_valid():
            video = form.save()
            
            # Handle constraint: if this video is active, deactivate others
            if video.is_active:
                HomePageVideo.objects.filter(is_active=True).exclude(id=video.id).update(is_active=False)
            
            messages.success(request, f'Home page video "{video.title}" updated successfully!')
            return redirect('admin_interface:admin_homepage_videos')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminHomePageVideoForm(instance=video)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Home Page Video: {video.title}',
        'video': video
    }
    return render(request, 'CustomAdmin/videos/video_form.html', context)

@login_required
def admin_homepage_video_delete(request, video_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    video = get_object_or_404(HomePageVideo, id=video_id, is_deleted=False)

    if request.method == 'POST':
        try:
            video_title = video.title
            video.delete()
            messages.success(request, f'Video "{video_title}" deleted successfully!')
            return redirect('admin_interface:admin_homepage_videos')
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('admin_interface:admin_homepage_videos')

    context = {
        'video': video,
        'title': f'Delete Video: {video.title}'
    }
    return render(request, 'CustomAdmin/videos/video_delete.html', context)

@login_required
def admin_homepage_video_restore(request, video_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    video = get_object_or_404(HomePageVideo.objects.all_with_deleted(), id=video_id)
    
    if request.method == 'POST':
        video_title = video.title
        video.restore()
        messages.success(request, f'Home page video "{video_title}" restored successfully!')
        return redirect('admin_interface:admin_homepage_videos')

    context = {
        'video': video,
        'title': f'Restore Home Page Video: {video.title}'
    }
    return render(request, 'CustomAdmin/videos/video_restore.html', context)

@login_required
def admin_homepage_video_permanent_delete(request, video_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    video = get_object_or_404(HomePageVideo.objects.all_with_deleted(), id=video_id)
    
    # Check if this is the last active video
    if video.is_active and HomePageVideo.objects.filter(is_active=True).count() <= 1:
        messages.error(request, 'Cannot permanently delete the last active video. Please activate another video first.')
        return redirect('admin_interface:admin_homepage_video_detail', video_id=video_id)
    
    if request.method == 'POST':
        video_title = video.title
        video.hard_delete()
        messages.success(request, f'Home page video "{video_title}" permanently deleted!')
        return redirect('admin_interface:admin_homepage_videos')

    context = {
        'video': video,
        'title': f'Permanently Delete Home Page Video: {video.title}'
    }
    return render(request, 'CustomAdmin/videos/video_permanent_delete.html', context)

@login_required
def admin_homepage_video_detail(request, video_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    video = get_object_or_404(HomePageVideo, id=video_id, is_deleted=False)

    context = {
        'video': video,
        'title': f'Home Page Video Details: {video.title}'
    }
    return render(request, 'CustomAdmin/videos/video_detail.html', context)

def export_homepage_videos_to_csv(videos):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="homepage_videos.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Title', 'Status', 'Created At', 'Updated At'])

    for video in videos:
        writer.writerow([
            video.id,
            video.title,
            'Active' if video.is_active else 'Inactive',
            video.created_at,
            video.updated_at,
        ])

    return response


def mark_messages_api(request):
    """API endpoint for marking messages as read/unread"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_ids = data.get('message_ids', [])
            action = data.get('action', '')
            
            if not message_ids or not action:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid request data'
                }, status=400)
            
            messages_to_update = ContactMessage.objects.filter(id__in=message_ids)
            
            if action == 'mark-read':
                updated_count = messages_to_update.update(
                    is_read=True,
                    read_at=timezone.now()
                )
                message = f'Successfully marked {updated_count} message(s) as read'
            elif action == 'mark-unread':
                updated_count = messages_to_update.update(
                    is_read=False,
                    read_at=None
                )
                message = f'Successfully marked {updated_count} message(s) as unread'
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid action'
                }, status=400)
            
            return JsonResponse({
                'success': True,
                'message': message
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)


@login_required
def admin_reply_to_contact(request, message_id):
    """Display reply form for a specific contact message"""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    message = get_object_or_404(ContactMessage, id=message_id, is_deleted=False)
    
    # Prepare initial reply subject
    if message.subject.lower().startswith('re:'):
        reply_subject = message.subject
    else:
        reply_subject = f"Re: {message.subject}"
    
    context = {
        'message': message,
        'reply_subject': reply_subject,
        'title': f'Reply to Message: {message.subject}'
    }
    return render(request, 'CustomAdmin/contacts/reply_form.html', context)


@login_required
def send_contact_reply(request):
    """Send a reply to a contact message"""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            message_id = data.get('message_id')
            subject = data.get('subject')
            message_content = data.get('message')
            mark_as_read = data.get('mark_as_read', True)
            
            if not all([message_id, subject, message_content]):
                return JsonResponse({
                    'success': False,
                    'error': 'Missing required fields'
                }, status=400)
            
            # Get the contact message
            contact_message = get_object_or_404(ContactMessage, id=message_id, is_deleted=False)
            
            # Create the reply record
            reply = ContactReply.objects.create(
                contact_message=contact_message,
                admin_user=request.user,
                subject=subject,
                message=message_content,
                recipient_email=contact_message.email,
                email_status='pending'
            )
            
            # Send the email
            try:
                from django.core.mail import send_mail
                from django.conf import settings
                
                # Create email content
                email_subject = subject
                email_message = f"""
Dear {contact_message.name},

Thank you for your message. Here is our response:

{message_content}

Best regards,
Factory InfoHub Team

---
Original Message:
Subject: {contact_message.subject}
From: {contact_message.name} ({contact_message.email})
Date: {contact_message.created_at.strftime('%B %d, %Y at %I:%M %p')}

{contact_message.message}
                """
                
                # Send email
                send_mail(
                    subject=email_subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[contact_message.email],
                    fail_silently=False,
                )
                
                # Mark reply as sent
                reply.mark_as_sent()
                
                # Mark message as read if requested
                if mark_as_read:
                    contact_message.mark_as_read()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Reply sent successfully!',
                    'reply_id': reply.id
                })
                
            except Exception as email_error:
                # Mark reply as failed
                reply.mark_as_failed(str(email_error))
                return JsonResponse({
                    'success': False,
                    'error': f'Failed to send email: {str(email_error)}'
                }, status=500)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    }, status=405)


@login_required
def admin_reply_history(request, message_id):
    """Display reply history for a specific contact message"""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    message = get_object_or_404(ContactMessage, id=message_id, is_deleted=False)
    replies = message.replies.filter(is_deleted=False).order_by('-sent_at')
    
    context = {
        'message': message,
        'replies': replies,
        'title': f'Reply History: {message.subject}'
    }
    return render(request, 'CustomAdmin/contacts/reply_history.html', context)


def admin_contact_detail(request, message_id):
    """
    Display detailed view of a contact message with reply functionality
    """
    message = get_object_or_404(ContactMessage, id=message_id)
    
    # Get all replies for this message
    replies = ContactReply.objects.filter(
        contact_message=message, 
        is_deleted=False
    ).select_related('admin_user').order_by('sent_at')
    
    # Get user information
    user_info = None
    if message.user:
        user_info = {
            'username': message.user.username,
            'email': message.user.email,
            'first_name': message.user.first_name,
            'last_name': message.user.last_name,
            'is_active': message.user.is_active,
            'date_joined': message.user.date_joined,
        }
    
    context = {
        'message': message,
        'replies': replies,
        'user_info': user_info,
        'total_replies': replies.count(),
    }
    
    return render(request, 'CustomAdmin/contacts/contact_detail.html', context)


# Payment Management Views
@login_required
def admin_payments(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    payment_status = request.GET.get('payment_status')
    payment_method = request.GET.get('payment_method')
    order_status = request.GET.get('order_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search', '')
    user_filter = request.GET.get('user')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    
    # 2. Build Queryset
    payments = Order.objects.select_related('user').order_by('-order_date')

    # Apply filters
    if payment_status:
        payments = payments.filter(payment_status=payment_status)
    if payment_method:
        payments = payments.filter(payment_method=payment_method)
    if order_status:
        payments = payments.filter(payment_status=order_status)
    if start_date:
        from django.utils import timezone
        from datetime import datetime
        # Convert naive date to timezone-aware datetime
        start_datetime = timezone.make_aware(datetime.combine(datetime.strptime(start_date, '%Y-%m-%d').date(), datetime.min.time()))
        payments = payments.filter(order_date__date__gte=start_datetime.date())
    if end_date:
        from django.utils import timezone
        from datetime import datetime
        # Convert naive date to timezone-aware datetime
        end_datetime = timezone.make_aware(datetime.combine(datetime.strptime(end_date, '%Y-%m-%d').date(), datetime.max.time()))
        payments = payments.filter(order_date__date__lte=end_datetime.date())
    if search:
        terms = search.split()
        payments = and_search_filter(
            payments,
            terms,
            ['order_number', 'user__username', 'user__email', 'transaction_id']
        )
    if user_filter:
        payments = payments.filter(user_id=user_filter)
    if min_amount:
        payments = payments.filter(total_amount__gte=min_amount)
    if max_amount:
        payments = payments.filter(total_amount__lte=max_amount)

    # 3. Calculate Summary Statistics
    total_payments = payments.count()
    completed_payments = payments.filter(payment_status='completed').count()
    pending_payments = payments.filter(payment_status='pending').count()
    failed_payments = payments.filter(payment_status='failed').count()

    # 4. CSV Export
    if 'download' in request.GET:
        return export_payments_to_csv(payments)

    # 5. Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(payments, 20)  # Show 20 payments per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 6. Get Users for Filter Dropdown
    users = User.objects.filter(orders__isnull=False).distinct()

    context = {
        'payments': page_obj,
        'users': users,
        'summary': {
            'total_payments': total_payments,
            'completed_payments': completed_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
        },
        'filters': {
            'payment_status': payment_status,
            'payment_method': payment_method,
            'order_status': order_status,
            'start_date': start_date,
            'end_date': end_date,
            'search': search,
            'user': user_filter,
            'min_amount': min_amount,
            'max_amount': max_amount,
        }
    }
    return render(request, 'CustomAdmin/payments/payments.html', context)

@login_required
def admin_payment_detail(request, order_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    
    order = get_object_or_404(Order, id=order_id)

    # Since there's no separate Payment model, we'll use the payment information from the Order model
    # Create a mock payment object using the order's payment fields
    class MockPayment:
        def __init__(self, order):
            self.order = order
            self.amount = order.total_amount
            self.currency = 'INR'  # Default currency
            self.transaction_id = order.transaction_id
            self.payment_method = order.payment_method
            self.status = order.payment_status
            self.created_at = order.order_date
            self.completed_at = order.order_date if order.payment_status == 'completed' else None
        
        def get_payment_method_display(self):
            payment_methods = {
                'card': 'Card',
                'upi': 'UPI',
                'netbanking': 'Net Banking',
                'cod': 'Cash on Delivery',
            }
            return payment_methods.get(self.payment_method, self.payment_method)
        
        def get_status_display(self):
            status_display = {
                'pending': 'Pending',
                'completed': 'Completed',
                'failed': 'Failed',
            }
            return status_display.get(self.status, self.status)

    payment = MockPayment(order)

    context = {
        'order': order,
        'payment': payment,
        'title': f'Payment Details - {order.order_number}'
    }
    return render(request, 'CustomAdmin/payments/payment_detail.html', context)

def export_payments_to_csv(payments):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Transaction ID', 'User', 'Email', 'Amount', 'Currency', 
        'Payment Method', 'Payment Status', 'Order Status', 'Created At', 'Completed At'
    ])

    for payment in payments:
        writer.writerow([
            payment.order.order_number,
            payment.transaction_id,
            payment.order.user.username,
            payment.order.user.email,
            payment.amount,
            payment.currency,
            payment.get_payment_method_display(),
            payment.get_status_display(),
            payment.order.get_payment_status_display(),
            payment.created_at,
            payment.completed_at if payment.completed_at else '',
        ])

    return response

@login_required
def admin_payment_gateways(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    
    
    gateways = PaymentGateway.objects.all()
    
    context = {
        'gateways': gateways,
        'title': 'Payment Gateways'
    }
    return render(request, 'CustomAdmin/payments/gateways.html', context)

@login_required
def admin_payment_gateway_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

   
   
    
    if request.method == 'POST':
        form = AdminPaymentGatewayForm(request.POST)
        if form.is_valid():
            gateway = form.save()
            messages.success(request, f'Payment gateway "{gateway.get_name_display()}" created successfully!')
            return redirect('admin_interface:admin_payment_gateways')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPaymentGatewayForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create Payment Gateway'
    }
    return render(request, 'CustomAdmin/payments/gateway_form.html', context)

@login_required
def admin_payment_gateway_edit(request, gateway_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    
    gateway = get_object_or_404(PaymentGateway, id=gateway_id)
    
    if request.method == 'POST':
        form = AdminPaymentGatewayForm(request.POST, instance=gateway)
        if form.is_valid():
            gateway = form.save()
            messages.success(request, f'Payment gateway "{gateway.get_name_display()}" updated successfully!')
            return redirect('admin_interface:admin_payment_gateways')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPaymentGatewayForm(instance=gateway)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Payment Gateway: {gateway.get_name_display()}',
        'gateway': gateway
    }
    return render(request, 'CustomAdmin/payments/gateway_form.html', context)

@login_required
def admin_payment_gateway_delete(request, gateway_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    
    gateway = get_object_or_404(PaymentGateway, id=gateway_id)
    
    if request.method == 'POST':
        gateway_name = gateway.get_name_display()
        gateway.delete()
        messages.success(request, f'Payment gateway "{gateway_name}" deleted successfully!')
        return redirect('admin_interface:admin_payment_gateways')

    context = {
        'gateway': gateway,
        'title': f'Delete Payment Gateway: {gateway.get_name_display()}'
    }
    return render(request, 'CustomAdmin/payments/gateway_delete.html', context)

@login_required
def admin_payment_gateway_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    
    if request.method == 'POST':
        form = AdminPaymentGatewayForm(request.POST)
        if form.is_valid():
            gateway = form.save()
            messages.success(request, f'Payment gateway "{gateway.get_name_display()}" created successfully!')
            return redirect('admin_interface:admin_payment_gateways')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPaymentGatewayForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create Payment Gateway'
    }
    return render(request, 'CustomAdmin/payments/gateway_form.html', context)

@login_required
def admin_payment_gateway_edit(request, gateway_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    
    gateway = get_object_or_404(PaymentGateway, id=gateway_id)
    
    if request.method == 'POST':
        form = AdminPaymentGatewayForm(request.POST, instance=gateway)
        if form.is_valid():
            gateway = form.save()
            messages.success(request, f'Payment gateway "{gateway.get_name_display()}" updated successfully!')
            return redirect('admin_interface:admin_payment_gateways')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPaymentGatewayForm(instance=gateway)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Payment Gateway: {gateway.get_name_display()}',
        'gateway': gateway
    }
    return render(request, 'CustomAdmin/payments/gateway_form.html', context)

@login_required
def admin_payment_gateway_delete(request, gateway_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')


    
    gateway = get_object_or_404(PaymentGateway, id=gateway_id)
    
    if request.method == 'POST':
        gateway_name = gateway.get_name_display()
        gateway.delete()
        messages.success(request, f'Payment gateway "{gateway_name}" deleted successfully!')
        return redirect('admin_interface:admin_payment_gateways')

    context = {
        'gateway': gateway,
        'title': f'Delete Payment Gateway: {gateway.get_name_display()}'
    }
    return render(request, 'CustomAdmin/payments/gateway_delete.html', context)

@login_required
def admin_orders(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

   
    

    # 1. Capture Filter Parameters
    payment_status = request.GET.get('payment_status')
    order_status = request.GET.get('order_status')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    search = request.GET.get('search', '')
    user_filter = request.GET.get('user')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    
    # 2. Build Queryset
    orders = Order.objects.select_related('user').order_by('-order_date')

    # Apply filters
    if payment_status:
        orders = orders.filter(payment_status=payment_status)
    if order_status:
        orders = orders.filter(payment_status=order_status)  # Using payment_status as order status
    if start_date:
        orders = orders.filter(order_date__date__gte=start_date)
    if end_date:
        orders = orders.filter(order_date__date__lte=end_date)
    if search:
        terms = search.split()
        orders = and_search_filter(
            orders,
            terms,
            ['order_number', 'user__username', 'user__email', 'transaction_id']
        )
    if user_filter:
        orders = orders.filter(user_id=user_filter)
    if min_amount:
        orders = orders.filter(total_amount__gte=min_amount)
    if max_amount:
        orders = orders.filter(total_amount__lte=max_amount)

    # 3. CSV Export
    if 'download' in request.GET:
        return export_orders_to_csv(orders)

    # 4. Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(orders, 20)  # Show 20 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 5. Get Users for Filter Dropdown
    users = User.objects.filter(orders__isnull=False).distinct()

    context = {
        'orders': page_obj,
        'users': users,
        'filters': {
            'payment_status': payment_status,
            'order_status': order_status,
            'start_date': start_date,
            'end_date': end_date,
            'search': search,
            'user': user_filter,
            'min_amount': min_amount,
            'max_amount': max_amount,
        }
    }
    return render(request, 'CustomAdmin/payments/orders.html', context)

@login_required
def admin_order_detail(request, order_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    order = get_object_or_404(Order, id=order_id)

    context = {
        'order': order,
        'title': f'Order Details - {order.id}'
    }
    return render(request, 'CustomAdmin/payments/order_detail.html', context)

@login_required
def admin_order_complete(request, order_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

   
    
    
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        try:
            # Mark order as completed
            order.payment_status = 'completed'
            order.save()
            
            # Clear cart
            cart = Cart.objects.get(user=order.user)
            cart.items.all().delete()
            
            # Send receipt
            factories = [item.factory for item in order.items.all()]
            send_order_receipt(order.user, order, factories)
            
            messages.success(request, f'Order {order.order_number} has been successfully completed.')
            return redirect('admin_interface:admin_payment_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return redirect('admin_interface:admin_payment_detail', order_id=order.id)

    context = {
        'order': order,
        'title': f'Complete Order - {order.order_number}'
    }
    return render(request, 'CustomAdmin/payments/order_complete.html', context)

@login_required
def admin_order_delete(request, order_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        try:
            order_number = order.order_number
            order.delete()
            messages.success(request, f'Order {order_number} has been successfully deleted.')
            return redirect('admin_interface:admin_orders')
        except Exception as e:
            messages.error(request, f'Error deleting order: {str(e)}')
            return redirect('admin_interface:admin_order_detail', order_id=order.id)

    context = {
        'order': order,
        'title': f'Delete Order - {order.order_number}'
    }
    return render(request, 'CustomAdmin/payments/order_delete.html', context)

@login_required
def admin_order_item_delete(request, item_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    order_item = get_object_or_404(OrderItem, id=item_id)
    
    if request.method == 'POST':
        try:
            factory_name = order_item.factory.name
            order_item.delete()
            messages.success(request, f'Order item for factory "{factory_name}" has been successfully deleted.')
            return redirect('admin_interface:admin_order_items')
        except Exception as e:
            messages.error(request, f'Error deleting order item: {str(e)}')
            return redirect('admin_interface:admin_order_item_detail', item_id=item_id)

    context = {
        'order_item': order_item,
        'title': f'Delete Order Item - {order_item.factory.name}'
    }
    return render(request, 'CustomAdmin/payments/order_item_delete.html', context)

@login_required
def admin_payment_gateway_delete(request, gateway_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    gateway = get_object_or_404(PaymentGateway, id=gateway_id)
    
    if request.method == 'POST':
        try:
            gateway_name = gateway.get_name_display()
            gateway.delete()
            messages.success(request, f'Payment gateway "{gateway_name}" has been successfully deleted.')
            return redirect('admin_interface:admin_payment_gateways')
        except Exception as e:
            messages.error(request, f'Error deleting payment gateway: {str(e)}')
            return redirect('admin_interface:admin_payment_gateway_edit', gateway_id=gateway.id)

    context = {
        'gateway': gateway,
        'title': f'Delete Payment Gateway - {gateway.get_name_display()}'
    }
    return render(request, 'CustomAdmin/payments/gateway_delete.html', context)

@login_required
def admin_order_items(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')
   

    # 1. Capture Filter Parameters
    order_filter = request.GET.get('order')
    factory_filter = request.GET.get('factory')
    search = request.GET.get('search', '')
    
    # 2. Build Queryset
    order_items = OrderItem.objects.select_related('order', 'factory', 'order__user').order_by('-order__order_date')

    # Apply filters
    if order_filter:
        order_items = order_items.filter(order_id=order_filter)
    if factory_filter:
        order_items = order_items.filter(factory_id=factory_filter)
    if search:
        terms = search.split()
        order_items = and_search_filter(
            order_items,
            terms,
            ['order__order_number', 'factory__name', 'order__user__username']
        )

    # 3. CSV Export
    if 'download' in request.GET:
        return export_order_items_to_csv(order_items)

    # 4. Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(order_items, 20)  # Show 20 order items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 5. Get Orders and Factories for Filter Dropdown
    orders = Order.objects.all()
    factories = Factory.objects.all()

    context = {
        'order_items': page_obj,
        'orders': orders,
        'factories': factories,
        'filters': {
            'order': order_filter,
            'factory': factory_filter,
            'search': search,
        }
    }
    return render(request, 'CustomAdmin/payments/order_items.html', context)

@login_required
def admin_order_item_detail(request, item_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')
    
    order_item = get_object_or_404(OrderItem, id=item_id)

    context = {
        'order_item': order_item,
        'title': f'Order Item Details - {order_item.factory.name}'
    }
    return render(request, 'CustomAdmin/payments/order_item_detail.html', context)

def export_orders_to_csv(orders):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'User', 'Email', 'Total Amount', 'Payment Status', 
        'Payment Method', 'Gateway Used', 'Transaction ID', 'Order Date', 'Receipt Sent'
    ])

    for order in orders:
        writer.writerow([
            order.order_number,
            order.user.username,
            order.user.email,
            order.total_amount,
            order.get_payment_status_display(),
            order.payment_method,
            order.gateway_used.get_name_display() if order.gateway_used else '',
            order.transaction_id,
            order.order_date,
            'Yes' if order.receipt_sent else 'No',
        ])

    return response

def export_order_items_to_csv(order_items):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="order_items.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Factory Name', 'Category', 'Price at Purchase', 'Order Date', 'User'
    ])

    for item in order_items:
        writer.writerow([
            item.order.order_number,
            item.factory.name,
            item.factory.category.name,
            item.price_at_purchase,
            item.order.order_date,
            item.order.user.username,
        ])

    return response

def export_payments_csv(request):
    """Export payments to CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Customer', 'Email', 'Amount', 'Currency', 'Status', 
        'Payment Method', 'Gateway', 'Transaction ID', 'Created At', 'Completed At'
    ])
    
    # Get filtered payments
    payments = PaymentGateway.objects.all().select_related('order', 'order__user', 'gateway_used')
    
    # Apply filters if present
    if request.GET.get('status'):
        payments = payments.filter(status=request.GET.get('status'))
    if request.GET.get('gateway'):
        payments = payments.filter(gateway_used_id=request.GET.get('gateway'))
    if request.GET.get('payment_method'):
        payments = payments.filter(payment_method=request.GET.get('payment_method'))
    if request.GET.get('search'):
        search_term = request.GET.get('search')
        payments = payments.filter(
            Q(order__order_number__icontains=search_term) |
            Q(order__user__username__icontains=search_term) |
            Q(order__user__email__icontains=search_term) |
            Q(transaction_id__icontains=search_term)
        )
    
    for payment in payments:
        writer.writerow([
            payment.order.order_number,
            payment.order.user.get_full_name() or payment.order.user.username,
            payment.order.user.email,
            payment.amount,
            payment.currency,
            payment.get_status_display(),
            payment.get_payment_method_display(),
            payment.gateway_used.name if payment.gateway_used else '',
            payment.transaction_id or '',
            payment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            payment.completed_at.strftime('%Y-%m-%d %H:%M:%S') if payment.completed_at else ''
        ])
    
    return response

def export_orders_csv(request):
    """Export orders to CSV"""
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Customer', 'Email', 'Total Amount', 'Payment Status', 
        'Payment Method', 'Transaction ID', 'Order Date', 'Items Count'
    ])
    
    # Get filtered orders
    orders = Order.objects.all().select_related('user')
    
    # Apply filters if present
    if request.GET.get('status'):
        orders = orders.filter(payment_status=request.GET.get('status'))
    if request.GET.get('payment_method'):
        orders = orders.filter(payment_method=request.GET.get('payment_method'))
    if request.GET.get('search'):
        search_term = request.GET.get('search')
        orders = orders.filter(
            Q(order_number__icontains=search_term) |
            Q(user__username__icontains=search_term) |
            Q(user__email__icontains=search_term) |
            Q(transaction_id__icontains=search_term)
        )
    
    for order in orders:
        writer.writerow([
            order.order_number,
            order.user.get_full_name() or order.user.username,
            order.user.email,
            order.total_amount,
            order.get_payment_status_display(),
            order.payment_method or '',
            order.transaction_id or '',
            order.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            order.items.count()
        ])
    
    return response

def export_order_items_csv(request):
    """Export order items to CSV"""
  
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="order_items_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Customer', 'Factory Name', 'Factory Location', 
        'Category', 'Price at Purchase', 'Order Date'
    ])
    
    # Get filtered order items
    order_items = OrderItem.objects.all().select_related('order', 'order__user', 'factory', 'factory__category')
    
    # Apply filters if present
    if request.GET.get('order'):
        order_items = order_items.filter(order_id=request.GET.get('order'))
    if request.GET.get('factory'):
        order_items = order_items.filter(factory_id=request.GET.get('factory'))
    if request.GET.get('search'):
        search_term = request.GET.get('search')
        order_items = order_items.filter(
            Q(order__order_number__icontains=search_term) |
            Q(order__user__username__icontains=search_term) |
            Q(order__user__email__icontains=search_term) |
            Q(factory__name__icontains=search_term)
        )
    
    for item in order_items:
        writer.writerow([
            item.order.order_number,
            item.order.user.get_full_name() or item.order.user.username,
            item.factory.name,
            f"{item.factory.city.name}, {item.factory.state.name}",
            item.factory.category.name,
            item.price_at_purchase,
            item.order.order_date.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    return response


@login_required
def admin_complete_order_with_email(request, order_id):
    """Complete an order and send email confirmation"""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        try:
            # Complete the order
            order.payment_status = 'completed'
            order.save()
            
            # Clear the user's cart
            try:
                cart = Cart.objects.get(user=order.user)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
            
            # Send email confirmation
            factories = [item.factory for item in order.items.all()]
            email_sent = send_order_receipt(order.user, order, factories)
            
            if email_sent:
                messages.success(request, f'Order {order.order_number} completed and email sent successfully!')
            else:
                messages.warning(request, f'Order {order.order_number} completed but email failed to send. You can retry sending the email from the order details page.')
            
            return redirect('admin_interface:admin_order_detail', order_id=order.id)
            
        except Exception as e:
            messages.error(request, f'Error completing order: {str(e)}')
            return redirect('admin_interface:admin_order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'title': f'Complete Order with Email - {order.order_number}'
    }
    return render(request, 'CustomAdmin/payments/order_complete_with_email.html', context)


@login_required
def admin_retry_order_email(request, order_id):
    """Retry sending order confirmation email"""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        try:
            factories = [item.factory for item in order.items.all()]
            email_sent = send_order_receipt(order.user, order, factories)
            
            if email_sent:
                messages.success(request, f'Email sent successfully for order {order.order_number}!')
            else:
                messages.error(request, f'Failed to send email for order {order.order_number}. Please check email configuration.')
            
        except Exception as e:
            messages.error(request, f'Error sending email: {str(e)}')
        
        return redirect('admin_interface:admin_order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'title': f'Retry Email - {order.order_number}'
    }
    return render(request, 'CustomAdmin/payments/retry_email.html', context)


@login_required
def admin_pending_orders(request):
    """Display pending orders that need attention"""
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    pending_orders = Order.objects.filter(payment_status='pending').order_by('-order_date')
    
    # Add email status information
    for order in pending_orders:
        order.email_status_display = dict(order._meta.get_field('email_status').choices).get(order.email_status, 'Unknown')
    
    context = {
        'pending_orders': pending_orders,
        'title': 'Pending Orders'
    }
    return render(request, 'CustomAdmin/payments/pending_orders.html', context)

 

@login_required
def factory_stats(request):
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('admin_interface:admin_dashboard')

    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    factories = Factory.objects.filter(is_deleted=False).annotate(
        total_view_count=Count('view_trackers'),
        today_view_count=Count('view_trackers', filter=Q(view_trackers__viewed_at__date=today)),
        weekly_view_count=Count('view_trackers', filter=Q(view_trackers__viewed_at__date__gte=week_ago)),
        monthly_view_count=Count('view_trackers', filter=Q(view_trackers__viewed_at__date__gte=month_ago))
    ).order_by('-total_view_count')

    context = {
        'stats': factories,
        'title': 'Factory View Statistics',
    }
    return render(request, 'CustomAdmin/FactoryStat/factory_stats.html', context)


@login_required
def factory_tracker_detail(request, factory_id):
    """Display detailed view trackers for a specific factory."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('admin_interface:admin_dashboard')

    factory = get_object_or_404(Factory, id=factory_id)
    trackers = FactoryViewTracker.objects.filter(factory=factory).order_by('-viewed_at')[:100]  # limit to 100 most recent
    context = {
        'factory': factory,
        'trackers': trackers,
        'title': f'View Trackers for {factory.name}',
    }
    return render(request, 'CustomAdmin/FactoryStat/factory_tracker_detail.html', context)


@login_required
def factory_stats_charts(request):
    """Display visual charts for factory view statistics."""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('admin_interface:admin_dashboard')

    # Get selected factory for line chart (default to first factory with stats)
    selected_factory_id = request.GET.get('factory')
    selected_factory = None
    if selected_factory_id:
        try:
            selected_factory = Factory.objects.get(id=selected_factory_id)
        except Factory.DoesNotExist:
            pass

    # If no factory selected, pick the one with the most views
    if not selected_factory:
        top_stats = FactoryViewStats.objects.select_related('factory').order_by('-total_views').first()
        if top_stats:
            selected_factory = top_stats.factory

    # Prepare data for the line chart (daily views for the last 30 days)
    line_chart_labels = []
    line_chart_data = []
    if selected_factory:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
        # Query trackers for the factory, grouped by day
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        daily_counts = (
            FactoryViewTracker.objects
            .filter(factory=selected_factory, viewed_at__date__gte=start_date)
            .annotate(day=TruncDate('viewed_at'))
            .values('day')
            .annotate(count=Count('id'))
            .order_by('day')
        )
        # Build lists for all 31 days (including days with zero views)
        date_dict = {d['day']: d['count'] for d in daily_counts}
        current = start_date
        while current <= end_date:
            line_chart_labels.append(current.strftime('%b %d'))
            line_chart_data.append(date_dict.get(current, 0))
            current += timedelta(days=1)

    # Prepare bar chart data for top 10 factories by total views
    top_factories = FactoryViewStats.objects.select_related('factory').order_by('-total_views')[:10]
    bar_labels = [stat.factory.name[:30] for stat in top_factories]  # truncate long names
    bar_data = [stat.total_views for stat in top_factories]

    context = {
        'title': 'Factory View Charts',
        'bar_labels': bar_labels,
        'bar_data': bar_data,
        'line_labels': line_chart_labels,
        'line_data': line_chart_data,
        'selected_factory': selected_factory,
        'factories': Factory.objects.filter(view_stats__isnull=False).order_by('name'),
    }
    return render(request, 'CustomAdmin/FactoryStat/factory_stats_charts.html', context)


# Page Management Views
@login_required
def admin_pages(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    page_type = request.GET.get('page_type')
    is_published = request.GET.get('is_published')
    search = request.GET.get('search', '')
    deleted_view = request.GET.get('deleted', 'active')  # 'active', 'deleted', 'all'

    # 2. Build Queryset
    pages = Page.objects.all_with_deleted().select_related()

    if page_type:
        pages = pages.filter(page_type=page_type)
    if is_published == 'published':
        pages = pages.filter(is_published=True)
    elif is_published == 'unpublished':
        pages = pages.filter(is_published=False)
    if search:
        pages = pages.filter(
            Q(title__icontains=search) |
            Q(slug__icontains=search) |
            Q(content__icontains=search) |
            Q(meta_title__icontains=search) |
            Q(meta_description__icontains=search)
        )

    # Filter by deleted status
    if deleted_view == 'deleted':
        pages = pages.filter(is_deleted=True)
    elif deleted_view == 'active':
        pages = pages.filter(is_deleted=False)

    # 3. CSV Export
    if 'download' in request.GET:
        return export_pages_to_csv(pages)

    # 4. Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(pages, 20)  # Show 20 pages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'pages': page_obj,
        'page_types': Page.PAGE_TYPES,
        'filters': {
            'page_type': page_type,
            'is_published': is_published,
            'search': search,
            'deleted': deleted_view,
        }
    }
    return render(request, 'CustomAdmin/pages/pages.html', context)

@login_required
def admin_page_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminPageForm(request.POST)
        if form.is_valid():
            page = form.save()
            messages.success(request, f'Page "{page.title}" created successfully!')
            return redirect('admin_interface:admin_pages')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPageForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New Page'
    }
    return render(request, 'CustomAdmin/pages/page_form.html', context)

@login_required
def admin_page_edit(request, page_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page = get_object_or_404(Page, id=page_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminPageForm(request.POST, instance=page)
        if form.is_valid():
            page = form.save()
            messages.success(request, f'Page "{page.title}" updated successfully!')
            return redirect('admin_interface:admin_pages')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPageForm(instance=page)

    # Get page sections for display
    page_sections = page.sections.all().order_by('order')

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Page: {page.title}',
        'page': page,
        'page_sections': page_sections
    }
    return render(request, 'CustomAdmin/pages/page_form.html', context)

@login_required
def admin_page_delete(request, page_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page = get_object_or_404(Page, id=page_id, is_deleted=False)
    
    if request.method == 'POST':
        page_title = page.title
        page.delete()
        messages.success(request, f'Page "{page_title}" deleted successfully!')
        return redirect('admin_interface:admin_pages')

    context = {
        'page': page,
        'title': f'Delete Page: {page.title}'
    }
    return render(request, 'CustomAdmin/pages/page_delete.html', context)

@login_required
def admin_page_restore(request, page_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page = get_object_or_404(Page.objects.all_with_deleted(), id=page_id)
    
    if request.method == 'POST':
        page_title = page.title
        page.restore()
        messages.success(request, f'Page "{page_title}" restored successfully!')
        return redirect('admin_interface:admin_pages')

    context = {
        'page': page,
        'title': f'Restore Page: {page.title}'
    }
    return render(request, 'CustomAdmin/pages/page_restore.html', context)

@login_required
def admin_page_permanent_delete(request, page_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page = get_object_or_404(Page.objects.all_with_deleted(), id=page_id)
    
    if request.method == 'POST':
        page_title = page.title
        page.hard_delete()
        messages.success(request, f'Page "{page_title}" permanently deleted successfully!')
        return redirect('admin_interface:admin_pages')

    context = {
        'page': page,
        'title': f'Permanently Delete Page: {page.title}'
    }
    return render(request, 'CustomAdmin/pages/page_permanent_delete.html', context)

@login_required
def admin_page_detail(request, page_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page = get_object_or_404(Page, id=page_id, is_deleted=False)
    page_sections = page.sections.all().order_by('order')

    context = {
        'page': page,
        'page_sections': page_sections,
        'title': f'Page Details: {page.title}'
    }
    return render(request, 'CustomAdmin/pages/page_detail.html', context)

@login_required
def admin_page_sections(request, page_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page = get_object_or_404(Page, id=page_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminPageSectionForm(request.POST)
        if form.is_valid():
            page_section = form.save()
            messages.success(request, f'Page section "{page_section.title}" added successfully!')
            return redirect('admin_interface:admin_page_sections', page_id=page.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPageSectionForm(initial={'page': page})

    page_sections = page.sections.all().order_by('order')

    context = {
        'page': page,
        'form': form,
        'page_sections': page_sections,
        'title': f'Manage Sections: {page.title}'
    }
    return render(request, 'CustomAdmin/pages/page_sections.html', context)

@login_required
def admin_page_section_edit(request, section_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page_section = get_object_or_404(PageSection, id=section_id)
    
    if request.method == 'POST':
        form = AdminPageSectionForm(request.POST, instance=page_section)
        if form.is_valid():
            page_section = form.save()
            messages.success(request, f'Page section "{page_section.title}" updated successfully!')
            return redirect('admin_interface:admin_page_sections', page_id=page_section.page.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminPageSectionForm(instance=page_section)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Section: {page_section.title}',
        'page_section': page_section
    }
    return render(request, 'CustomAdmin/pages/page_section_form.html', context)

@login_required
def admin_page_section_delete(request, section_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    page_section = get_object_or_404(PageSection, id=section_id)
    
    if request.method == 'POST':
        section_title = page_section.title
        page_section.delete()
        messages.success(request, f'Page section "{section_title}" deleted successfully!')
        return redirect('admin_interface:admin_page_sections', page_id=page_section.page.id)

    context = {
        'page_section': page_section,
        'title': f'Delete Section: {page_section.title}'
    }
    return render(request, 'CustomAdmin/pages/page_section_delete.html', context)

def export_pages_to_csv(pages):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pages.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID', 'Title', 'Slug', 'Page Type', 'Published', 'Created At', 'Updated At'
    ])

    for page in pages:
        writer.writerow([
            page.id,
            page.title,
            page.slug,
            page.get_page_type_display(),
            'Yes' if page.is_published else 'No',
            page.created_at,
            page.updated_at,
        ])

    return response
