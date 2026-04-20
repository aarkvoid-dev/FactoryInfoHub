from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.db import transaction,models
from django.utils import timezone
from .email_service import FactoryEmailService
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms import inlineformset_factory
from django.http import Http404
from decimal import Decimal
import json
import logging
import smtplib
import traceback
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from .models import Factory,Cart, CartItem, Order, OrderItem, Factory,PaymentGateway, FactoryViewStats,FactoryImage
from blog.models import BlogPost
from .forms import FactoryForm, FactoryFilterForm, FactoryImageFormSet, CategoryForm, SubCategoryForm, CountryForm, StateForm, CityForm, DistrictForm, RegionForm
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from Accounts.decorators import email_verified_required, allow_unverified
from django.contrib.admin.views.decorators import staff_member_required

import stripe
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ValidationError
from django.utils.decorators import method_decorator
import razorpay

# Initialize Stripe API key from database
def get_stripe_api_key():
    """Get Stripe API key from the active payment gateway"""
    try:
        gateway = PaymentGateway.objects.get(is_active=True, name='stripe')
        return gateway.key_secret
    except PaymentGateway.DoesNotExist:
        return None

def get_stripe_publishable_key():
    """Get Stripe publishable key from the active payment gateway"""
    try:
        gateway = PaymentGateway.objects.get(is_active=True, name='stripe')
        return gateway.key_id
    except PaymentGateway.DoesNotExist:
        return None

def get_stripe_client():
    """Get configured Stripe client with lazy initialization"""
    api_key = get_stripe_api_key()
    if api_key:
        stripe.api_key = api_key
        return stripe
    else:
        return None

# Configure logging
logger = logging.getLogger(__name__)

# Import payment logging functions
from .logging_config import (
    log_payment_attempt, log_payment_success, log_payment_failure,
    log_webhook_received, log_webhook_processed, log_webhook_error,
    log_email_sent, log_email_failed, log_security_event, log_performance_metric
)

def get_active_gateway():
    try:
        return PaymentGateway.objects.get(is_active=True)
    except PaymentGateway.DoesNotExist:
        return None

def validate_payment_gateway_config():
    """Validate that payment gateway is properly configured"""
    try:
        gateway = PaymentGateway.objects.get(is_active=True)
        if not gateway.key_id or not gateway.key_secret:
            raise ValueError("Payment gateway API keys not configured")
        return gateway
    except PaymentGateway.DoesNotExist:
        raise ValueError("No active payment gateway configured")
    except Exception as e:
        raise ValueError(f"Payment gateway configuration error: {str(e)}")


def factory_list(request):
    """List all factories with filtering and search"""
    # Only show user's factories if user is authenticated
    # if request.user.is_authenticated:
    #     factories = Factory.objects.filter(Q(is_active=True, is_deleted=False,is_verified=True) | Q(created_by=request.user)).select_related(
    #         'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    #     )
    # else:
    #     # For anonymous users, only show public factories
    #     factories = Factory.objects.filter(is_active=True, is_deleted=False, is_verified=True).select_related(
    #         'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    #     )

    factories = Factory.objects.filter(Q(is_active=True, is_deleted=False)).select_related(
            'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
        )
    
    # Get cart items count for authenticated users
    cart_items_count = 0
    cart_items = []
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.items.count()
            cart_items = list(cart.items.values_list('factory_id', flat=True))
        except Cart.DoesNotExist:
            pass
    
    # Prepare initial data for form based on GET parameters
    initial_data = {}
    if 'category' in request.GET:
        try:
            category_id = int(request.GET.get('category'))
            initial_data['category'] = category_id
        except (ValueError, TypeError):
            pass
    
    if 'subcategory' in request.GET:
        try:
            subcategory_id = int(request.GET.get('subcategory'))
            initial_data['subcategory'] = subcategory_id
        except (ValueError, TypeError):
            pass
    
    if 'country' in request.GET:
        try:
            country_id = int(request.GET.get('country'))
            initial_data['country'] = country_id
        except (ValueError, TypeError):
            pass
    
    if 'state' in request.GET:
        try:
            state_id = int(request.GET.get('state'))
            initial_data['state'] = state_id
        except (ValueError, TypeError):
            pass
    
    if 'city' in request.GET:
        try:
            city_id = int(request.GET.get('city'))
            initial_data['city'] = city_id
        except (ValueError, TypeError):
            pass
    
    if 'district' in request.GET:
        try:
            district_id = int(request.GET.get('district'))
            initial_data['district'] = district_id
        except (ValueError, TypeError):
            pass
    
    if 'region' in request.GET:
        try:
            region_id = int(request.GET.get('region'))
            initial_data['region'] = region_id
        except (ValueError, TypeError):
            pass
    
    # Apply filters
    filter_form = FactoryFilterForm(request.GET, initial=initial_data)
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        subcategory = filter_form.cleaned_data.get('subcategory')
        country = filter_form.cleaned_data.get('country')
        state = filter_form.cleaned_data.get('state')
        city = filter_form.cleaned_data.get('city')
        district = filter_form.cleaned_data.get('district')
        region = filter_form.cleaned_data.get('region')
        factory_type = filter_form.cleaned_data.get('factory_type')
        

        if category:
            factories = factories.filter(category=category)
        if subcategory:
            factories = factories.filter(subcategory=subcategory)
        if country:
            factories = factories.filter(country=country)
        if state:
            factories = factories.filter(state=state)
        if city:
            factories = factories.filter(city=city)
        if district:
            factories = factories.filter(district=district)
        if region:
            factories = factories.filter(region=region)
        if factory_type:
            factories = factories.filter(factory_type__icontains=factory_type)
        

    # Apply search with AND for multi-word queries
    search_query = request.GET.get('search', '')
    if search_query:
        terms = search_query.split()
        q_objects = Q()
        for term in terms:
            term_q = (
                Q(name__icontains=term) |
                Q(description__icontains=term) |
                Q(address__icontains=term) |
                Q(contact_person__icontains=term) |
                Q(factory_type__icontains=term)
            )
            q_objects &= term_q
        factories = factories.filter(q_objects)

    sort_by = request.GET.get('sort', 'name')
    if sort_by in ['name', 'created_at', 'updated_at']:
        factories = factories.order_by(sort_by)
    elif sort_by == 'category':
        factories = factories.order_by('category__name', 'name')
    elif sort_by == 'location':
        factories = factories.order_by('country__name', 'state__name', 'city__name', 'name')

    # Pagination
    paginator = Paginator(factories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    is_paginated = page_obj.has_other_pages()
     # Get random published blog posts for slider
    random_blogs = BlogPost.objects.filter(
        is_published=True,
        is_deleted=False
    ).order_by('?')[:8]  # 6 random posts

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'search_query': search_query,
        'sort_by': sort_by,
        'cart_items_count': cart_items_count,
        'cart_items': cart_items,
        'random_blogs': random_blogs,   # add this line
        'is_paginated': is_paginated,
    }
    return render(request, 'karkahan/factory_list.html', context)

def process_hierarchical_fields(data):
    """
    Takes a mutable QueryDict (POST copy) and replaces any new names
    with existing or newly created object IDs for hierarchical fields.
    Modifies the dictionary in place and returns it.
    """
    # --- Category ---
    cat_val = data.get('category')
    if cat_val and not cat_val.isdigit():
        cat = Category.objects.filter(name__iexact=cat_val).first()
        if not cat:
            cat = Category.objects.create(name=cat_val, is_active=True)
        data['category'] = str(cat.id)

    # --- Subcategory (depends on category) ---
    sub_val = data.get('subcategory')
    if sub_val and not sub_val.isdigit():
        cat_id = data.get('category')
        if cat_id and cat_id.isdigit():
            sub = SubCategory.objects.filter(name__iexact=sub_val, category_id=cat_id).first()
            if not sub:
                sub = SubCategory.objects.create(name=sub_val, category_id=cat_id, is_active=True)
            data['subcategory'] = str(sub.id)

    # --- Country ---
    country_val = data.get('country')
    if country_val and not country_val.isdigit():
        country = Country.objects.filter(name__iexact=country_val).first()
        if not country:
            country = Country.objects.create(name=country_val)
        data['country'] = str(country.id)

    # --- State (depends on country) ---
    state_val = data.get('state')
    if state_val and not state_val.isdigit():
        country_id = data.get('country')
        if country_id and country_id.isdigit():
            state = State.objects.filter(name__iexact=state_val, country_id=country_id).first()
            if not state:
                state = State.objects.create(name=state_val, country_id=country_id)
            data['state'] = str(state.id)

    # --- City (depends on state) ---
    city_val = data.get('city')
    if city_val and not city_val.isdigit():
        state_id = data.get('state')
        if state_id and state_id.isdigit():
            city = City.objects.filter(name__iexact=city_val, state_id=state_id).first()
            if not city:
                city = City.objects.create(name=city_val, state_id=state_id)
            data['city'] = str(city.id)

    # --- District (depends on city) ---
    district_val = data.get('district')
    if district_val and not district_val.isdigit():
        city_id = data.get('city')
        if city_id and city_id.isdigit():
            district = District.objects.filter(name__iexact=district_val, city_id=city_id).first()
            if not district:
                district = District.objects.create(name=district_val, city_id=city_id)
            data['district'] = str(district.id)

    # --- Region (depends on district) ---
    region_val = data.get('region')
    if region_val and not region_val.isdigit():
        district_id = data.get('district')
        if district_id and district_id.isdigit():
            region = Region.objects.filter(name__iexact=region_val, district_id=district_id).first()
            if not region:
                region = Region.objects.create(name=region_val, district_id=district_id)
            data['region'] = str(region.id)

    return data

@email_verified_required
@login_required
def factory_create(request):
    """Create a new factory with dynamic category/location creation"""
    if request.method == 'POST':
        # Create a mutable copy of POST and process new names
        post_data = request.POST.copy()
        post_data = process_hierarchical_fields(post_data)

        form = FactoryForm(post_data)
        formset = FactoryImageFormSet(request.POST, request.FILES)  # original POST for images

        if form.is_valid() and formset.is_valid():
            from django.db import transaction
            try:
                with transaction.atomic():
                    # Save the factory with the current user as created_by
                    factory = form.save(commit=False)
                    factory.created_by = request.user
                    factory.save()
                    
                    # Save the formset with the factory instance
                    formset.instance = factory
                    formset.save()

                    # Set a default primary image if none exists
                    if factory.images.exists() and not factory.images.filter(is_primary=True).exists():
                        first_image = factory.images.first()
                        first_image.is_primary = True
                        first_image.save()

                messages.success(request, f'Factory "{factory.name}" has been created successfully!')
                return redirect('karkahan:factory_detail', slug=factory.slug)
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
    else:
        form = FactoryForm()
        formset = FactoryImageFormSet()

    context = {
        'form': form,
        'formset': formset,
        'title': 'Add New Factory',
    }
    return render(request, 'karkahan/factory_form.html', context)


def factory_creator_or_admin_required(view_func):
    """Decorator to check if user is admin or factory creator"""
    def _wrapped_view(request, slug, *args, **kwargs):
        factory = get_object_or_404(Factory, slug=slug, is_deleted=False)
        
        # Check if user is admin or the creator of the factory
        if not (request.user.is_staff or request.user == factory.created_by):
            messages.error(request, "You don't have permission to edit this factory.")
            return redirect('karkahan:factory_detail', slug=slug)
        
        return view_func(request, slug, *args, **kwargs)
    return _wrapped_view


@login_required
@factory_creator_or_admin_required
def factory_edit(request, slug):
    factory = get_object_or_404(Factory, slug=slug, is_deleted=False)

    if request.method == 'POST':
        # Create a mutable copy of POST and process new names
        post_data = request.POST.copy()
        post_data = process_hierarchical_fields(post_data)

        form = FactoryForm(post_data, instance=factory)
        formset = FactoryImageFormSet(request.POST, request.FILES, instance=factory, prefix='images')
        print(form.errors)
        if form.is_valid() and formset.is_valid():

            # factory = form.save()
            # formset.save()
            factory = form.save(commit=False)

            # If the current user is not admin, reset verified status
            if not (request.user.is_staff or request.user.is_superuser):
                factory.is_verified = False

            # Now save the factory
            factory.save()
            form.save_m2m()          # Save many-to-many fields if any
            formset.save()

            # Handle image operations
            handle_image_operations(request, factory)

            messages.success(request, f'Factory "{factory.name}" updated!')
            return redirect('karkahan:factory_detail', slug=factory.slug)
    else:
        form = FactoryForm(instance=factory)
        formset = FactoryImageFormSet(instance=factory, prefix='images')

    context = {
        'form': form,
        'formset': formset,
        'factory': factory,
        'title': 'Edit Factory',
    }
    return render(request, 'karkahan/factory_form.html', context)


def handle_image_operations(request, factory):
    """
    Handle image operations including:
    - Setting primary images
    - Removing primary status from images
    - Adding new images
    - Deleting images
    """
    # Handle primary image selection
    primary_image_id = request.POST.get('primary_image')
    if primary_image_id:
        try:
            primary_image = factory.images.get(id=primary_image_id)
            # Remove primary status from all other images
            factory.images.update(is_primary=False)
            # Set the selected image as primary
            primary_image.is_primary = True
            primary_image.save()
        except FactoryImage.DoesNotExist:
            pass

    # Handle removing primary status
    remove_primary_id = request.POST.get('remove_primary')
    if remove_primary_id:
        try:
            image_to_remove_primary = factory.images.get(id=remove_primary_id)
            if image_to_remove_primary.is_primary:
                image_to_remove_primary.is_primary = False
                image_to_remove_primary.save()
                
                # If no primary image exists, set the first image as primary
                if not factory.images.filter(is_primary=True).exists() and factory.images.exists():
                    first_image = factory.images.first()
                    first_image.is_primary = True
                    first_image.save()
        except FactoryImage.DoesNotExist:
            pass

    # Handle new image uploads
    new_images = request.FILES.getlist('new_images')
    if new_images:
        for image_file in new_images:
            FactoryImage.objects.create(
                factory=factory,
                image=image_file,
                alt_text=f"Image for {factory.name}",
                is_primary=False  # Will be handled separately
            )

    # Ensure only one primary image exists
    ensure_single_primary_image(factory)


def ensure_single_primary_image(factory):
    """Ensure that exactly one image is marked as primary"""
    primary_count = factory.images.filter(is_primary=True).count()
    
    if primary_count == 0 and factory.images.exists():
        # Set the first image as primary if none exists
        first_image = factory.images.first()
        first_image.is_primary = True
        first_image.save()
    elif primary_count > 1:
        # Remove primary status from all but the first primary image
        primary_images = factory.images.filter(is_primary=True)
        first_primary = primary_images.first()
        primary_images.exclude(pk=first_primary.pk).update(is_primary=False)

@login_required
def factory_delete(request, slug):
    """Delete a factory (soft delete)"""
    try:
        factory = Factory.objects.get(slug=slug)
    except Factory.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Factory not found.'})
        messages.error(request, 'Factory not found.')
        return redirect('karkahan:factory_list')
    
    if factory.is_deleted:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Factory is already deleted.'})
        messages.error(request, 'This factory has already been deleted.')
        return redirect('karkahan:factory_list')
    
    # Check if user has permission to delete (admin or factory creator)
    if not (request.user.is_staff or request.user == factory.created_by):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': "You don't have permission to delete this factory."})
        messages.error(request, "You don't have permission to delete this factory.")
        return redirect('karkahan:factory_detail', slug=slug)
    
    if request.method == 'POST':
        factory.delete()  # Soft delete (SoftDeleteModel overrides delete to soft delete)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': f'Factory "{factory.name}" has been deleted successfully!'})
        messages.success(request, f'Factory "{factory.name}" has been deleted successfully!')
        return redirect('karkahan:factory_list')
    
    context = {
        'factory': factory,
    }
    return render(request, 'karkahan/factory_confirm_delete.html', context)


@login_required
def factory_restore(request, slug):
    """Restore a soft-deleted factory (superuser only)"""
    if not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': "You don't have permission to restore factories."})
        messages.error(request, "You don't have permission to restore factories.")
        return redirect('karkahan:factory_list')
    
    factory = get_object_or_404(Factory, slug=slug, is_deleted=True)
    
    if request.method == 'POST':
        factory.restore()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': f'Factory "{factory.name}" has been restored successfully!'})
        messages.success(request, f'Factory "{factory.name}" has been restored successfully!')
        return redirect('karkahan:factory_detail', slug=factory.slug)
    
    context = {
        'factory': factory,
    }
    return render(request, 'karkahan/factory_confirm_restore.html', context)


@login_required
def factory_hard_delete(request, slug):
    """Permanently delete a factory (superuser only)"""
    try:
        factory = Factory.objects.get(slug=slug)
    except Factory.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'Factory not found.'})
        messages.error(request, 'Factory not found.')
        return redirect('karkahan:factory_list')
    
    if not request.user.is_superuser:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': "You don't have permission to permanently delete factories."})
        messages.error(request, "You don't have permission to permanently delete factories.")
        return redirect('karkahan:factory_list')
    
    if request.method == 'POST':
        factory_name = factory.name
        factory.hard_delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': True, 'message': f'Factory "{factory_name}" has been permanently deleted!'})
        messages.success(request, f'Factory "{factory_name}" has been permanently deleted!')
        return redirect('karkahan:factory_list')
    
    context = {
        'factory': factory,
    }
    return render(request, 'karkahan/factory_confirm_hard_delete.html', context)


@login_required
@factory_creator_or_admin_required
def factory_toggle_active(request, slug):
    """Toggle factory active status"""
    factory = get_object_or_404(Factory, slug=slug, is_deleted=False)
    factory.is_active = not factory.is_active
    factory.save()
    
    status = "activated" if factory.is_active else "deactivated"
    messages.success(request, f'Factory "{factory.name}" has been {status} successfully!')
    return redirect('karkahan:factory_detail', slug=factory.slug)


@login_required
@factory_creator_or_admin_required
def factory_toggle_verified(request, slug):
    """Toggle factory verified status"""
    factory = get_object_or_404(Factory, slug=slug, is_deleted=False)
    factory.is_verified = not factory.is_verified
    factory.save()
    
    status = "verified" if factory.is_verified else "unverified"
    messages.success(request, f'Factory "{factory.name}" has been {status} successfully!')
    return redirect('karkahan:factory_detail', slug=factory.slug)


def dashboard(request):
    """Factory dashboard with statistics including view counts"""
    total_factories = Factory.objects.filter(is_deleted=False).count()
    active_factories = Factory.objects.filter(is_active=True, is_deleted=False).count()
    verified_factories = Factory.objects.filter(is_verified=True, is_deleted=False).count()
    categories_with_factories = Category.objects.filter(
        factories__isnull=False,
        factories__is_deleted=False
    ).distinct().count()
    
    # View statistics
    total_views = FactoryViewStats.objects.aggregate(
        total=models.Sum('total_views')
    )['total'] or 0
    
    today_views = FactoryViewStats.objects.aggregate(
        today=models.Sum('today_views')
    )['today'] or 0
    
    # Most viewed factory
    most_viewed_factory = FactoryViewStats.objects.select_related('factory').order_by('-total_views').first()
    
    # Recent factories with view counts
    recent_factories = Factory.objects.filter(is_deleted=False).prefetch_related(
        'view_stats'
    ).order_by('-created_at')[:5]
    
    context = {
        'total_factories': total_factories,
        'active_factories': active_factories,
        'verified_factories': verified_factories,
        'categories_with_factories': categories_with_factories,
        'recent_factories': recent_factories,
        'total_views': total_views,
        'today_views': today_views,
        'most_viewed_factory': most_viewed_factory.factory if most_viewed_factory else None,
        'most_viewed_count': most_viewed_factory.total_views if most_viewed_factory else 0,
    }
    return render(request, 'karkahan/dashboard.html', context)


# AJAX views for dynamic form updates
def get_subcategories(request):
    """Get subcategories for a given category"""
    category_id = request.GET.get('category_id')
    subcategories = SubCategory.objects.filter(
        category_id=category_id,
        is_active=True
    ).values('id', 'name')
    return JsonResponse(list(subcategories), safe=False)


def get_states(request):
    """Get states for a given country"""
    country_id = request.GET.get('country_id')
    states = State.objects.filter(country_id=country_id).values('id', 'name')
    return JsonResponse(list(states), safe=False)


def get_cities(request):
    """Get cities for a given state"""
    state_id = request.GET.get('state_id')
    cities = City.objects.filter(state_id=state_id).values('id', 'name')
    return JsonResponse(list(cities), safe=False)


def get_districts(request):
    """Get districts for a given city"""
    city_id = request.GET.get('city_id')
    districts = District.objects.filter(city_id=city_id).values('id', 'name')
    return JsonResponse(list(districts), safe=False)


def get_regions(request):
    """Get regions for a given district"""
    district_id = request.GET.get('district_id')
    regions = Region.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)


# Factory Detail with Purchase Logic
def factory_detail(request, slug):
    """Display factory details with purchase options"""
    
    factory = get_object_or_404(Factory, slug=slug)
    
    # if not factory.is_active and not request.user.is_staff:
    #     messages.warning(request,f"{slug} - This factory is currently inactive.")
    #     return redirect('karkahan:factory_list')
    # Track factory view (only track for non-admin users to avoid skewing stats)
    if not request.user.is_staff:
        from .utils import track_factory_view
        track_factory_view(factory, request)
    
    # Get related factories (same category, excluding current factory)
    # related_factories = Factory.objects.filter(
    #     category=factory.category,
    #     is_active=True,
    #     is_deleted=False
    # ).exclude(slug=factory.slug).order_by('?')[:3]

    related_factories = Factory.objects.filter(
        category=factory.category,
        is_deleted=False
    ).exclude(slug=factory.slug).order_by('?')[:3]

    user_has_purchased = False
    if request.user.is_authenticated:
        user_has_purchased = OrderItem.objects.filter(
            order__user=request.user,
            factory=factory,
            order__payment_status='completed'
        ).exists()
    
    # Get view statistics (only for admin users)
    view_stats = None
    if request.user.is_staff:
        from .utils import get_factory_view_stats
        view_stats = get_factory_view_stats(factory)
    
    context = {
        'factory': factory,
        'related_factories': related_factories,
        'user_has_purchased': user_has_purchased,
        'view_stats': view_stats,
    }
    return render(request, 'karkahan/factory_detail.html', context)


# Email Testing View
@login_required
def test_email(request):
    """Test email functionality"""
    if request.method == 'POST':
        try:
            # Send test email
            send_mail(
                subject='Test Email from Factory InfoHub',
                message='This is a test email to verify the email system is working correctly.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[request.user.email],
                fail_silently=False,
            )
            messages.success(request, f"Test email sent successfully to {request.user.email}")
        except Exception as e:
            messages.error(request, f"Failed to send test email: {str(e)}")
        
        return redirect('karkahan:test_email')
    
    context = {
        'user_email': request.user.email,
        'email_backend': settings.EMAIL_BACKEND,
        'email_host': getattr(settings, 'EMAIL_HOST', 'Not set'),
        'email_port': getattr(settings, 'EMAIL_PORT', 'Not set'),
        'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', 'Not set'),
        'email_host_user': getattr(settings, 'EMAIL_HOST_USER', 'Not set'),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set'),
    }
    return render(request, 'karkahan/test_email.html', context)



# ---------------------------
# Cart Management
# ---------------------------

@email_verified_required
@login_required
def add_to_cart(request, factory_slug):
    factory = get_object_or_404(Factory, slug=factory_slug, is_active=True, is_deleted=False)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, factory=factory)
    if created:
        messages.success(request, f'Added "{factory.name}" to your cart.')
    else:
        messages.info(request, f'"{factory.name}" is already in your cart.')
    return redirect('karkahan:cart_detail')


@email_verified_required
@login_required
@require_POST
def add_to_cart_api(request, factory_slug):
    """API endpoint to add factory to cart without redirecting"""
    try:
        factory = get_object_or_404(Factory, slug=factory_slug, is_active=True, is_deleted=False)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        item, created = CartItem.objects.get_or_create(cart=cart, factory=factory)
        
        if created:
            return JsonResponse({
                'success': True,
                'message': f'Added "{factory.name}" to your cart.',
                'cart_count': cart.items.count(),
                'in_cart': True
            })
        else:
            return JsonResponse({
                'success': True,
                'message': f'"{factory.name}" is already in your cart.',
                'cart_count': cart.items.count(),
                'in_cart': True
            })
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': 'Failed to add factory to cart.',
            'error': str(e)
        }, status=500)


@email_verified_required
@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    factory_name = cart_item.factory.name
    cart_item.delete()
    messages.success(request, f'Removed "{factory_name}" from your cart.')
    return redirect('karkahan:cart_detail')


@email_verified_required
@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    context = {'cart': cart}
    return render(request, 'Cart/cart_detail.html', context)


# ---------------------------
# Checkout & Payment
# ---------------------------
# Note: Old checkout function removed - use initiate_checkout instead



@login_required
@require_POST
def initiate_checkout(request):
    """Enhanced AJAX endpoint: creates order and returns gateway-specific data with comprehensive error handling."""
    try:
        # Validate cart
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return JsonResponse({'error': 'Your cart is empty.'}, status=400)

        # Validate gateway configuration
        try:
            gateway = validate_payment_gateway_config()
        except ValueError as e:
            logger.error(f"Payment gateway validation failed: {e}")
            return JsonResponse({'error': str(e)}, status=500)

        # Validate cart items still exist and are active
        for item in cart.items.all():
            if not item.factory.is_active or item.factory.is_deleted:
                return JsonResponse({'error': 'One or more items in your cart are no longer available.'}, status=400)

        # Create order with transaction safety
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=cart.total_price,
                payment_status='pending',
                gateway_used=gateway
            )

            # Create order items
            for item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    factory=item.factory,
                    price_at_purchase=item.factory.price
                )

        # Process payment based on gateway
        if gateway.name == 'stripe':
            return process_stripe_payment(request, order, gateway)
        elif gateway.name == 'razorpay':
            return process_razorpay_payment(request, order, gateway)
        else:
            return JsonResponse({'error': 'Unsupported gateway'}, status=500)

    except Exception as e:
        logger.error(f"Checkout error: {e}")
        return JsonResponse({'error': 'Payment processing failed. Please try again.'}, status=500)

def process_stripe_payment(request, order, gateway):
    """Process Stripe payment with enhanced error handling"""
    try:
        stripe_client = get_stripe_client()
        if not stripe_client:
            raise ValueError("Stripe API key not configured")
        
        line_items = []
        for item in order.items.all():
            line_items.append({
                'price_data': {
                    'currency': 'inr',
                    'unit_amount': int(item.factory.price * 100),
                    'product_data': {'name': item.factory.name},
                },
                'quantity': 1,
            })
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(reverse('karkahan:checkout_success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('karkahan:cart_detail')),
            metadata={'order_id': order.id},
        )
        
        order.transaction_id = checkout_session.id
        order.save()
        
        return JsonResponse({
            'gateway': 'stripe',
            'session_url': checkout_session.url
        })
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe API error: {e}")
        order.payment_status = 'failed'
        order.save()
        return JsonResponse({'error': f'Stripe payment failed: {str(e)}'}, status=500)
    except Exception as e:
        logger.error(f"Stripe payment processing error: {e}")
        order.payment_status = 'failed'
        order.save()
        return JsonResponse({'error': 'Payment processing failed'}, status=500)

def process_razorpay_payment(request, order, gateway):
    """Process Razorpay payment with enhanced error handling"""
    try:
        # Validate Razorpay configuration
        if not gateway.key_id or not gateway.key_secret:
            return JsonResponse({'error': 'Razorpay configuration incomplete. Please contact administrator.'}, status=500)
        
        client = razorpay.Client(auth=(gateway.key_id, gateway.key_secret))
        razorpay_order = client.order.create({
            'amount': int(order.total_amount * 100),   # in paise
            'currency': 'INR',
            'receipt': f'order_{order.id}',
            'payment_capture': 1
        })
        
        order.transaction_id = razorpay_order['id']
        order.save()
        
        return JsonResponse({
            'gateway': 'razorpay',
            'order_id': razorpay_order['id'],
            'key_id': gateway.key_id,
            'amount': float(order.total_amount),   # frontend expects number
            'currency': 'INR',
            'name': 'Factory Chemistry',
            'description': 'Factory purchase',
            'image': '',  # optional logo URL
            'prefill': {
                'name': request.user.get_full_name() or request.user.username,
                'email': request.user.email,
                'contact': '',  # optional phone
            },
            'theme': {'color': '#EB662B'},
        })
        
    except razorpay.errors.BadRequestError as e:
        logger.error(f"Razorpay bad request error: {e}")
        order.payment_status = 'failed'
        order.save()
        return JsonResponse({'error': f'Razorpay configuration error: {str(e)}'}, status=500)
    except razorpay.errors.ServerError as e:
        logger.error(f"Razorpay server error: {e}")
        order.payment_status = 'failed'
        order.save()
        return JsonResponse({'error': 'Razorpay server error. Please try again later.'}, status=500)
    except Exception as e:
        logger.error(f"Razorpay payment processing error: {e}")
        order.payment_status = 'failed'
        order.save()
        return JsonResponse({'error': 'Payment processing failed'}, status=500)


def checkout_success(request):
    """Enhanced checkout success page with order status verification and email management"""
    session_id = request.GET.get('session_id')
    razorpay_payment_id = request.GET.get('razorpay_payment_id')
    
    # Find the most recent order for this user
    latest_order = Order.objects.filter(user=request.user).order_by('-order_date').first()
    
    if not latest_order:
        messages.error(request, 'No recent order found.')
        return redirect('karkahan:cart_detail')
    
    # Verify payment status
    payment_verified = False
    payment_error = None
    
    if session_id:
        # Stripe success - verify session
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid':
                payment_verified = True
                # Mark payment as completed (money transferred)
                latest_order.payment_completed = True
                latest_order.save()
                
                # Send email and mark order as completed if email succeeds
                factories = [item.factory for item in latest_order.items.all()]
                email_sent = send_order_receipt(request.user, latest_order, factories)
                
                if email_sent:
                    latest_order.payment_status = 'completed'
                    latest_order.save()
            else:
                payment_error = f"Payment not completed. Status: {session.payment_status}"
        except Exception as e:
            payment_error = f"Could not verify Stripe payment: {str(e)}"
    elif razorpay_payment_id:
        # Razorpay success - verify payment
        try:
            gateway = get_active_gateway()
            if gateway and gateway.name == 'razorpay':
                client = razorpay.Client(auth=(gateway.key_id, gateway.key_secret))
                payment = client.payment.fetch(razorpay_payment_id)
                if payment['status'] == 'captured':
                    payment_verified = True
                    # Mark payment as completed (money transferred)
                    latest_order.payment_completed = True
                    latest_order.save()
                    
                    # Send email and mark order as completed if email succeeds
                    factories = [item.factory for item in latest_order.items.all()]
                    email_sent = send_order_receipt(request.user, latest_order, factories)
                    
                    if email_sent:
                        latest_order.payment_status = 'completed'
                        latest_order.save()
                else:
                    payment_error = f"Payment not captured. Status: {payment['status']}"
        except Exception as e:
            payment_error = f"Could not verify Razorpay payment: {str(e)}"
    else:
        # No payment method specified, check order status
        if latest_order.payment_completed:
            payment_verified = True
        else:
            payment_error = "Payment status could not be verified."
    
    # Handle email sending if payment was successful but email not sent
    email_sent = False
    email_error = None
    
    if payment_verified and latest_order.email_status in ['pending', 'retry', 'failed']:
        factories = [item.factory for item in latest_order.items.all()]
        email_sent = send_order_receipt(request.user, latest_order, factories)
        
        if not email_sent:
            email_error = "Email sending failed. You can retry sending the email from your order history."
    
    # Prepare context
    context = {
        'order': latest_order,
        'payment_verified': payment_verified,
        'payment_error': payment_error,
        'email_sent': email_sent,
        'email_error': email_error,
        'factories': [item.factory for item in latest_order.items.all()],
    }
    
    return render(request, 'Cart/checkout_success.html', context)


# ---------------------------
# Stripe Webhook
# ---------------------------

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Stripe webhook endpoint – fetches secret from active gateway."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    # 1. Get the active Stripe gateway from the database
    gateway = get_active_gateway()
    if not gateway or gateway.name != 'stripe':
        logging.error("No active Stripe gateway configured")
        return HttpResponse(status=400)
    
    # 2. Use the gateway's webhook secret
    webhook_secret = gateway.webhook_secret
    if not webhook_secret:
        logging.error("Stripe gateway has no webhook secret configured")
        return HttpResponse(status=400)

    # 3. Construct the event
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        logging.error(f"Invalid Stripe webhook payload: {e}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logging.error(f"Invalid Stripe webhook signature: {e}")
        return HttpResponse(status=400)
    except Exception as e:
        logging.error(f"Unexpected error in Stripe webhook: {e}")
        return HttpResponse(status=500)

    # 4. Handle events (same as before)
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        try:
            handle_successful_checkout(session)
        except Exception as e:
            logging.error(f"Error handling successful checkout: {e}")
            return HttpResponse(status=500)
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        try:
            handle_successful_payment(payment_intent)
        except Exception as e:
            logging.error(f"Error handling successful payment: {e}")
            return HttpResponse(status=500)

    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    """Razorpay webhook to update order status."""
    gateway = get_active_gateway()
    if not gateway or gateway.name != 'razorpay':
        logging.error("Razorpay webhook: No active Razorpay gateway configured")
        return HttpResponse(status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        logging.error(f"Razorpay webhook: Invalid JSON payload: {e}")
        return HttpResponse(status=400)

    event = data.get('event')
    logging.info(f"Razorpay webhook: Received event {event}")
    
    if event == 'payment.captured':
        payment = data.get('payload', {}).get('payment', {}).get('entity', {})
        razorpay_order_id = payment.get('order_id')
        razorpay_payment_id = payment.get('id')
        
        logging.info(f"Razorpay webhook: Processing payment {razorpay_payment_id} for order {razorpay_order_id}")
        
        try:
            order = Order.objects.get(transaction_id=razorpay_order_id)
            
            # Only update if not already processed to prevent duplicate processing
            if order.payment_completed != True:
                # Mark payment as completed (money transferred)
                order.payment_completed = True
                order.save()
                
                # Clear cart
                cart = Cart.objects.get(user=order.user)
                cart.items.all().delete()
                
                # Send receipt
                factories = [item.factory for item in order.items.all()]
                email_sent = send_order_receipt(order.user, order, factories)
                
                # Only mark order as completed if email was sent successfully
                if email_sent:
                    order.payment_status = 'completed'
                    order.save()
                
                logging.info(f"Razorpay webhook: Order {order.id} payment completed, email sent: {email_sent}")
            else:
                logging.info(f"Razorpay webhook: Order {order.id} already processed, skipping")
                
        except Order.DoesNotExist:
            logging.error(f"Razorpay webhook: Order with transaction_id {razorpay_order_id} not found")
        except Exception as e:
            logging.error(f"Razorpay webhook: Error processing order {razorpay_order_id}: {str(e)}")
            # Rollback order status if something failed
            if 'order' in locals():
                order.payment_completed = False
                order.save()

    return HttpResponse(status=200)



def handle_successful_checkout(session):
    metadata = session.get('metadata', {})
    order_id = metadata.get('order_id')
    if not order_id:
        logging.error(f"Stripe webhook: No order_id found in metadata: {metadata}")
        return

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        logging.error(f"Stripe webhook: Order {order_id} not found")
        return

    # Only update if not already processed to prevent duplicate processing
    if order.payment_completed != True:
        try:
            # Mark payment as completed (money transferred)
            order.payment_completed = True
            order.transaction_id = session.get('id')  # or payment_intent
            order.stripe_payment_intent = session.get('payment_intent')
            order.save()

            # Clear cart
            cart = Cart.objects.get(user=order.user)
            cart.items.all().delete()

            # Send receipt (factories = order.items.all() is a queryset of OrderItem, need factory list)
            factories = [item.factory for item in order.items.all()]
            email_sent = send_order_receipt(order.user, order, factories)
            
            # Only mark order as completed if email was sent successfully
            if email_sent:
                order.payment_status = 'completed'
                order.save()
            
            logging.info(f"Stripe webhook: Order {order_id} payment completed, email sent: {email_sent}")
        except Exception as e:
            logging.error(f"Stripe webhook: Error processing order {order_id}: {str(e)}")
            # Rollback order status if something failed
            order.payment_completed = False
            order.save()


def send_order_receipt(user, order, factories, retry_count=0):
    """Send order receipt email with improved error handling and retry logic"""
    try:
        subject = f"Your Factory InfoHub Order #{order.order_number}"
        context = {
            'user': user,
            'order': order,
            'factories': factories,  # This is already a list of all factories in the order
        }
        
        # Render email templates
        html_message = render_to_string('emails/order_receipt.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email with error handling - ONE EMAIL PER ORDER
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False
        )
        
        # Mark as sent successfully - ONE EMAIL PER ORDER
        order.receipt_sent = True
        order.email_status = 'sent'
        order.email_sent_at = timezone.now()
        order.email_retry_count = retry_count
        order.last_email_error = None
        order.save()
        
        logging.info(f"Order receipt sent successfully to {user.email} for order {order.order_number} with {len(factories)} factories")
        return True
        
    except Exception as e:
        # Log the error
        error_message = f"Failed to send order receipt to {user.email} for order {order.order_number}: {str(e)}"
        logging.error(error_message)
        
        # Update order with error information
        order.email_status = 'failed' if retry_count >= 2 else 'retry'
        order.email_retry_count = retry_count + 1
        order.last_email_error = str(e)[:500]  # Truncate long error messages
        order.save()
        
        # Try fallback email backend if available
        try:
            from django.core.mail import get_connection
            from django.core.mail.backends.console import EmailBackend
            
            # Try console backend as fallback
            connection = get_connection(backend='django.core.mail.backends.console.EmailBackend')
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                connection=connection
            )
            logging.info(f"Order receipt sent via console backend to {user.email} for order {order.order_number}")
            
            # Mark as sent via fallback
            order.receipt_sent = True
            order.email_status = 'sent'
            order.email_sent_at = timezone.now()
            order.last_email_error = None
            order.save()
            
            return True
        except Exception as fallback_error:
            fallback_error_message = f"Fallback email sending also failed for order {order.order_number}: {str(fallback_error)}"
            logging.error(fallback_error_message)
            
            # Update with final failure
            order.email_status = 'failed'
            order.last_email_error = f"{str(e)[:250]} | Fallback: {str(fallback_error)[:250]}"
            order.save()
            
            return False


def handle_successful_payment(payment_intent):
    """Handle successful payment intent (alternative to checkout session)"""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    metadata = payment_intent.get('metadata', {})
    user_id = metadata.get('user_id')
    cart_id = metadata.get('cart_id')

    if not user_id or not cart_id:
        return

    try:
        user = User.objects.get(id=user_id)
        cart = Cart.objects.get(id=cart_id, user=user)
    except (User.DoesNotExist, Cart.DoesNotExist):
        return

    total = cart.total_price

    # Create order
    order = Order.objects.create(
        user=user,
        total_amount=total,
        payment_status='completed',
        stripe_payment_intent=payment_intent.get('id')
    )

    # Create order items and collect factories for email
    purchased_factories = []
    for cart_item in cart.items.all():
        OrderItem.objects.create(
            order=order,
            factory=cart_item.factory,
            price_at_purchase=cart_item.factory.price
        )
        purchased_factories.append(cart_item.factory)

    # Clear the cart
    cart.items.all().delete()

    # Send email
    send_order_receipt(user, order, purchased_factories)


# ---------------------------
# Order History
# ---------------------------

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-order_date')
    context = {'orders': orders}
    return render(request, 'Cart/order_history.html', context)


@staff_member_required
def factory_purchase_history(request, factory_id):
    """Display all purchases of a specific factory (admin only)."""
    factory = get_object_or_404(Factory, id=factory_id)
    # Get all completed order items for this factory
    order_items = OrderItem.objects.filter(
        factory=factory,
        order__payment_status='completed'
    ).select_related('order', 'order__user').order_by('-order__order_date')
    
    context = {
        'factory': factory,
        'order_items': order_items,
        'title': f'Purchase History - {factory.name}',
    }
    return render(request, 'Cart/factory_purchase_history.html', context)


# ---------------------------
# Payment Error Handling
# ---------------------------

@login_required
def payment_failed(request):
    """Handle payment failures and provide user feedback"""
    error_message = request.GET.get('error', 'Payment processing failed. Please try again.')
    context = {
        'error_message': error_message,
    }
    return render(request, 'Cart/payment_failed.html', context)


@login_required
def retry_payment(request, order_id):
    """Allow users to retry failed payments"""
    order = get_object_or_404(Order, id=order_id, user=request.user, payment_status='failed')
    
    # Create new order with same items
    cart, _ = Cart.objects.get_or_create(user=request.user)
    
    # Clear existing cart items
    cart.items.all().delete()
    
    # Add items from failed order to cart
    for item in order.items.all():
        CartItem.objects.get_or_create(cart=cart, factory=item.factory)
    
    # Delete the failed order
    order.delete()
    
    messages.info(request, 'Your previous order has been cancelled. Please proceed with checkout again.')
    return redirect('karkahan:cart_detail')


@login_required
def resend_order_email(request, order_id):
    """Allow users to resend order email"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Check if email can be resent (not already sent successfully)
    if order.email_status == 'sent':
        messages.warning(request, 'Email has already been sent successfully for this order.')
        return redirect('karkahan:order_history')
    
    # Get factories for the order
    factories = [item.factory for item in order.items.all()]
    
    # Attempt to send email with retry logic
    email_sent = send_order_receipt(request.user, order, factories, retry_count=order.email_retry_count)
    
    if email_sent:
        messages.success(request, f'Email has been resent successfully for order #{order.order_number}.')
    else:
        messages.error(request, f'Failed to resend email for order #{order.order_number}. Please contact support.')
    
    return redirect('karkahan:order_history')


@login_required
def reinitiate_payment(request, order_id):
    """Allow users to reinitiate payment for pending orders"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only allow reinitiation for pending orders
    if order.payment_status != 'pending':
        messages.error(request, f'Cannot reinitiate payment for order #{order.order_number}. Status: {order.get_payment_status_display()}')
        return redirect('karkahan:order_history')
    
    # Validate gateway configuration
    try:
        gateway = validate_payment_gateway_config()
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('karkahan:order_history')
    
    # Process payment based on gateway
    if gateway.name == 'stripe':
        return process_stripe_payment(request, order, gateway)
    elif gateway.name == 'razorpay':
        return process_razorpay_payment(request, order, gateway)
    else:
        messages.error(request, 'Unsupported payment gateway')
        return redirect('karkahan:order_history')


@login_required
def verify_payment_status(request, order_id):
    """Allow users to verify payment status for their orders"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Only verify for pending orders
    if order.payment_status != 'pending':
        messages.info(request, f'Order #{order.order_number} is already {order.get_payment_status_display()}.')
        return redirect('karkahan:order_history')
    
    # Get active gateway
    gateway = get_active_gateway()
    if not gateway:
        messages.error(request, 'No payment gateway is currently configured.')
        return redirect('karkahan:order_history')
    
    verification_successful = False
    error_message = None
    
    try:
        if gateway.name == 'stripe':
            # Verify Stripe payment
            if order.transaction_id:
                session = stripe.checkout.Session.retrieve(order.transaction_id)
                if session.payment_status == 'paid':
                    # Mark payment as completed (money transferred)
                    order.payment_completed = True
                    order.save()
                    
                    # Send email and mark order as completed if email succeeds
                    cart = Cart.objects.get(user=request.user)
                    cart.items.all().delete()
                    
                    factories = [item.factory for item in order.items.all()]
                    email_sent = send_order_receipt(request.user, order, factories)
                    
                    if email_sent:
                        order.payment_status = 'completed'
                        order.save()
                        verification_successful = True
                        messages.success(request, f'Payment verified successfully for order #{order.order_number}. Email sent to {request.user.email}.')
                    else:
                        error_message = "Payment verified but email sending failed. You can retry sending the email from your order history."
                else:
                    error_message = f"Payment not completed. Status: {session.payment_status}"
            else:
                error_message = "No Stripe session ID found for this order."
                
        elif gateway.name == 'razorpay':
            # Verify Razorpay payment
            if order.transaction_id:
                client = razorpay.Client(auth=(gateway.key_id, gateway.key_secret))
                payment = client.payment.fetch(order.transaction_id)
                if payment['status'] == 'captured':
                    # Mark payment as completed (money transferred)
                    order.payment_completed = True
                    order.save()
                    
                    # Send email and mark order as completed if email succeeds
                    cart = Cart.objects.get(user=request.user)
                    cart.items.all().delete()
                    
                    factories = [item.factory for item in order.items.all()]
                    email_sent = send_order_receipt(request.user, order, factories)
                    
                    if email_sent:
                        order.payment_status = 'completed'
                        order.save()
                        verification_successful = True
                        messages.success(request, f'Payment verified successfully for order #{order.order_number}. Email sent to {request.user.email}.')
                    else:
                        error_message = "Payment verified but email sending failed. You can retry sending the email from your order history."
                else:
                    error_message = f"Payment not captured. Status: {payment['status']}"
            else:
                error_message = "No Razorpay payment ID found for this order."
        else:
            error_message = "Unsupported payment gateway for verification."
            
    except Exception as e:
        error_message = f"Error verifying payment: {str(e)}"
        logger.error(f"Payment verification error for order {order_id}: {e}")
    
    if not verification_successful and error_message:
        messages.error(request, f'Payment verification failed: {error_message}')
    elif verification_successful:
        messages.success(request, f'Payment verified successfully for order #{order.order_number}.')
    
    return redirect('karkahan:order_history')


@login_required
def report_payment_issue(request, order_id):
    """Allow users to report payment issues"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    # Create a support message or log the issue
    issue_description = f"""
    Payment Issue Report
    ===================
    
    Order Details:
    - Order ID: {order.id}
    - Order Number: {order.order_number}
    - User: {request.user.username} ({request.user.email})
    - Order Date: {order.order_date}
    - Payment Status: {order.payment_status}
    - Email Status: {order.email_status}
    - Transaction ID: {order.transaction_id}
    - Gateway Used: {order.gateway_used.name if order.gateway_used else 'None'}
    
    User Description:
    [User can add description here]
    
    System Information:
    - IP Address: {request.META.get('REMOTE_ADDR', 'Unknown')}
    - User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}
    - Timestamp: {timezone.now()}
    """
    
    # Log the issue
    logger.warning(f"Payment issue reported for order {order.order_number} by user {request.user.username}")
    
    # Send notification email to admin (optional)
    try:
        send_mail(
            subject=f'Payment Issue Reported - Order #{order.order_number}',
            message=issue_description,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.DEFAULT_FROM_EMAIL],  # Send to admin
            fail_silently=True,
        )
    except Exception as e:
        logger.error(f"Failed to send payment issue notification: {e}")
    
    messages.success(request, f'Thank you for reporting the issue. We have logged your payment problem for order #{order.order_number}. Our support team will review it and get back to you.')
    
    return redirect('karkahan:order_history')


