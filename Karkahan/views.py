from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login
from django.urls import reverse, reverse_lazy
from django.db import transaction
from django.utils import timezone
from .email_service import FactoryEmailService
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.forms import inlineformset_factory
from django.http import Http404
from django.core.exceptions import ValidationError
from decimal import Decimal
import json
import logging

def can_make_purchase(user):
    """
    Check if user can make purchases based on email verification status.
    
    Staff and superusers can always make purchases.
    Regular users must have verified email to make purchases.
    
    Args:
        user: Django User object
        
    Returns:
        bool: True if user can make purchases, False otherwise
    """
    if not user.is_authenticated:
        return False
    
    # Staff and superusers can always make purchases
    if user.is_staff or user.is_superuser:
        return True
    
    # Check if user has a profile and email is verified
    try:
        profile = user.profile
        return profile.email_verified
    except:
        # If no profile exists, user cannot make purchases
        return False


def get_email_verification_message(user):
    """
    Get a user-friendly message about email verification status.
    
    Args:
        user: Django User object
        
    Returns:
        str: User-friendly message about email verification
    """
    if not user.is_authenticated:
        return "Please log in to make purchases."
    
    # Staff and superusers don't need email verification
    if user.is_staff or user.is_superuser:
        return "You have admin privileges and can make purchases."
    
    # Check if user has a profile
    try:
        profile = user.profile
        if profile.email_verified:
            return "Your email is verified. You can make purchases."
        else:
            return "Please verify your email address to make purchases. Check your email for a verification link."
    except:
        return "Please complete your profile setup to make purchases."

from .models import Factory, ShoppingCart, FactoryPurchase, PurchaseHistory, Order, OrderItem, Payment
from .forms import FactoryForm, FactoryFilterForm, FactoryImageFormSet, CategoryForm, SubCategoryForm, CountryForm, StateForm, CityForm, DistrictForm, RegionForm, ShoppingCartForm, CheckoutForm, OrderForm, PaymentForm
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region


def factory_list(request):
    """List all factories with filtering and search"""
    factories = Factory.objects.filter(is_active=True, is_deleted=False,is_verified=True).select_related(
        'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    )
    
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
        

    # Apply search
    search_query = request.GET.get('search', '')
    if search_query:
        factories = factories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(factory_type__icontains=search_query)
        )


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

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'search_query': search_query,
        'sort_by': sort_by,
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
                    factory = form.save()
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

        if form.is_valid() and formset.is_valid():
            factory = form.save()
            formset.save()

            # Ensure only one primary image
            primary_count = factory.images.filter(is_primary=True).count()
            if primary_count == 0 and factory.images.exists():
                first_image = factory.images.first()
                first_image.is_primary = True
                first_image.save()
            elif primary_count > 1:
                primary_images = factory.images.filter(is_primary=True)
                first_primary = primary_images.first()
                primary_images.exclude(pk=first_primary.pk).update(is_primary=False)

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

@login_required
@factory_creator_or_admin_required
def factory_delete(request, slug):
    """Delete a factory (soft delete)"""
    factory = get_object_or_404(Factory, slug=slug, is_deleted=False)
    
    if request.method == 'POST':
        factory.soft_delete()
        messages.success(request, f'Factory "{factory.name}" has been deleted successfully!')
        return redirect('karkahan:factory_list')
    
    context = {
        'factory': factory,
    }
    return render(request, 'karkahan/factory_confirm_delete.html', context)


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
    """Factory dashboard with statistics"""
    total_factories = Factory.objects.filter(is_deleted=False).count()
    active_factories = Factory.objects.filter(is_active=True, is_deleted=False).count()
    verified_factories = Factory.objects.filter(is_verified=True, is_deleted=False).count()
    categories_with_factories = Category.objects.filter(
        factories__isnull=False,
        factories__is_deleted=False
    ).distinct().count()
    
    # Recent factories
    recent_factories = Factory.objects.filter(is_deleted=False).order_by('-created_at')[:5]
    
    context = {
        'total_factories': total_factories,
        'active_factories': active_factories,
        'verified_factories': verified_factories,
        'categories_with_factories': categories_with_factories,
        'recent_factories': recent_factories,
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


# ENHANCED SHOPPING CART VIEWS

@login_required
def add_to_cart(request, factory_slug):
    """Add a factory to the shopping cart with proper validation"""
    factory = get_object_or_404(Factory, slug=factory_slug, is_active=True, is_deleted=False)
    
    # Check if user can make purchases (email verification)
    if not can_make_purchase(request.user):
        messages.error(request, "Please verify your email address before adding items to cart.")
        return redirect('karkahan:factory_detail', slug=factory_slug)
    
    # Check if already purchased
    if factory.has_user_purchased(request.user):
        messages.warning(request, 'You have already purchased this factory.')
        return redirect('karkahan:factory_detail', slug=factory_slug)
    
    # Check if already in cart
    cart_item, created = ShoppingCart.objects.get_or_create(
        user=request.user,
        factory=factory,
        defaults={'quantity': 1}
    )
    
    if not created:
        # Item already exists in cart, increment quantity
        if cart_item.quantity < 10:  # Max quantity limit
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f'Quantity updated for {factory.name}. Now {cart_item.quantity} in cart.')
        else:
            messages.warning(request, f'Maximum quantity limit reached for {factory.name}.')
    else:
        messages.success(request, f'Added {factory.name} to your cart.')
    
    return redirect('karkahan:cart_view')


@login_required
def remove_from_cart(request, cart_item_id):
    """Remove an item from the shopping cart"""
    cart_item = get_object_or_404(ShoppingCart, id=cart_item_id, user=request.user)
    factory_name = cart_item.factory.name
    cart_item.delete()
    messages.success(request, f"{factory_name} has been removed from your cart!")
    return redirect('karkahan:cart_view')


@login_required
@require_POST
def update_cart_quantity(request, cart_item_id):
    """Update quantity of an item in the cart via AJAX"""
    cart_item = get_object_or_404(ShoppingCart, id=cart_item_id, user=request.user)
    
    try:
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
            messages.success(request, f"Item removed from cart.")
            return JsonResponse({'success': True, 'removed': True})
        elif quantity > 10:
            messages.error(request, "Maximum quantity per item is 10.")
            return JsonResponse({'success': False, 'error': 'Maximum quantity per item is 10.'})
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f"Quantity updated for {cart_item.factory.name}.")
            return JsonResponse({'success': True, 'new_quantity': quantity})
    
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid quantity value.'})


@login_required
def cart_view(request):
    """View the shopping cart with enhanced functionality"""
    cart_items = ShoppingCart.objects.filter(user=request.user).select_related('factory')
    subtotal = ShoppingCart.get_cart_total(request.user)
    cart_count = ShoppingCart.get_cart_count(request.user)
    
    # Calculate tax and total for display
    tax_amount = subtotal * Decimal('0.18')  # 18% GST
    service_fee = Decimal('0.0')  # No service fee for now
    total_amount = subtotal + tax_amount + service_fee
    
    context = {
        'cart_items': cart_items,
        'total_price': subtotal,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'cart_count': cart_count,
    }
    return render(request, 'karkahan/cart.html', context)


@login_required
def clear_cart(request):
    """Clear all items from the shopping cart"""
    cart_items = ShoppingCart.objects.filter(user=request.user)
    count = cart_items.count()
    cart_items.delete()
    
    if count > 0:
        messages.success(request, f"Cleared {count} item(s) from your cart.")
    else:
        messages.info(request, "Your cart is already empty.")
    
    return redirect('karkahan:cart_view')


# ENHANCED CHECKOUT AND ORDER VIEWS

@login_required
def checkout(request):
    """Enhanced checkout page with order creation"""
    cart_items = ShoppingCart.objects.filter(user=request.user).select_related('factory')
    
    if not cart_items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect('karkahan:factory_list')
    
    # Check if user can make purchases (email verification)
    if not can_make_purchase(request.user):
        messages.error(request, "Please verify your email address before proceeding to checkout.")
        return redirect('karkahan:cart_view')
    
    # Calculate totals
    subtotal = ShoppingCart.get_cart_total(request.user)
    tax_amount = subtotal * Decimal('0.18')  # 18% GST
    service_fee = Decimal('0.0')
    total_amount = subtotal + tax_amount + service_fee
    
    # Initialize checkout form
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        customer_name=form.cleaned_data['customer_name'],
                        customer_email=form.cleaned_data['customer_email'],
                        customer_phone=form.cleaned_data['customer_phone'],
                        payment_method=form.cleaned_data['payment_method'],
                        subtotal=subtotal,
                        tax_amount=tax_amount,
                        service_fee=service_fee,
                        total_amount=total_amount,
                        status='pending',
                        payment_status='pending'
                    )
                    
                    # Create order items
                    for cart_item in cart_items:
                        OrderItem.objects.create(
                            order=order,
                            factory=cart_item.factory,
                            quantity=cart_item.quantity,
                            price_at_purchase=cart_item.factory.price
                        )
                    
                    # Create payment record
                    payment = Payment.objects.create(
                        order=order,
                        payment_method=form.cleaned_data['payment_method'],
                        amount=total_amount,
                        currency='INR',
                        status='pending'
                    )
                    
                    # Clear cart
                    cart_items.delete()
                    
                    messages.success(request, f"Order {order.order_number} created successfully!")
                    return redirect('karkahan:order_detail', order_id=order.id)
                    
            except Exception as e:
                messages.error(request, f"An error occurred while creating your order: {str(e)}")
                return redirect('karkahan:checkout')
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'tax_amount': tax_amount,
        'service_fee': service_fee,
        'total_amount': total_amount,
        'form': form,
    }
    return render(request, 'karkahan/checkout.html', context)


@login_required
def order_detail(request, order_id):
    """View order details"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    context = {
        'order': order,
    }
    return render(request, 'karkahan/order_detail.html', context)


@login_required
def order_list(request):
    """List user's orders"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'karkahan/order_list.html', context)


@login_required
def payment_page(request, order_id):
    """Payment page for a specific order (New Order-based Payment)"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.payment_status in ['completed', 'refunded']:
        messages.info(request, "This order has already been paid for.")
        return redirect('karkahan:order_detail', order_id=order.id)
    
    # Check if user can make purchases (email verification)
    if not can_make_purchase(request.user):
        messages.error(request, "Please verify your email address before making payments.")
        return redirect('karkahan:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        payment_method = request.POST.get('payment_method')
        if payment_method:
            try:
                from .payment_utils import PaymentProcessor
                
                # Process payment using payment utilities
                success = PaymentProcessor.complete_order_payment(order, payment_method)
                
                if success:
                    messages.success(request, "Payment completed successfully!")
                    return redirect('karkahan:order_detail', order_id=order.id)
                else:
                    messages.error(request, "Payment processing failed.")
                    
            except Exception as e:
                messages.error(request, f"Payment processing failed: {str(e)}")
    
    context = {
        'order': order,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'karkahan/payment.html', context)


@login_required
def legacy_payment_page(request, purchase_amount):
    """Legacy payment page for individual factory purchases"""
    # This is for backward compatibility with old payment flow
    # In a real implementation, you might want to redirect to new system
    # or handle legacy purchases differently
    
    # Check if user can make purchases (email verification)
    if not can_make_purchase(request.user):
        messages.error(request, "Please verify your email address before making purchases.")
        return redirect('karkahan:factory_list')
    
    try:
        # Try to find a pending purchase for this user with the given amount
        pending_purchase = FactoryPurchase.objects.filter(
            user=request.user,
            payment_status='pending',
            price_at_purchase=purchase_amount
        ).first()
        
        if not pending_purchase:
            messages.error(request, "No pending purchase found for this amount.")
            return redirect('karkahan:factory_list')
        
        context = {
            'purchase': pending_purchase,
            'amount': purchase_amount,
            'formatted_amount': f"Rs. {purchase_amount:,.2f}",
            'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
        }
        return render(request, 'karkahan/legacy_payment.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading payment page: {str(e)}")
        return redirect('karkahan:factory_list')


@login_required
def cancel_order(request, order_id):
    """Cancel an order"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if order.status in ['completed', 'cancelled', 'refunded']:
        messages.error(request, "This order cannot be cancelled.")
        return redirect('karkahan:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                order.status = 'cancelled'
                order.payment_status = 'cancelled'
                order.save()
                
                # Refund payment if already completed
                payment = order.payments.first()
                if payment and payment.status == 'completed':
                    payment.status = 'refunded'
                    payment.refunded_amount = payment.amount
                    payment.refunded_at = timezone.now()
                    payment.save()
                
                messages.success(request, f"Order {order.order_number} has been cancelled.")
                
        except Exception as e:
            messages.error(request, f"Failed to cancel order: {str(e)}")
    
    return redirect('karkahan:order_detail', order_id=order.id)


# ENHANCED EMAIL SYSTEM - Using centralized email service

def send_order_confirmation_email(order):
    """Send order confirmation email using centralized email service"""
    return FactoryEmailService.send_order_confirmation_email(order)


# LEGACY VIEWS (for backward compatibility)

@login_required
def process_purchase(request):
    """Legacy purchase processing (deprecated - use checkout instead)"""
    # Check if user can make purchases (email verification)
    if not can_make_purchase(request.user):
        messages.error(request, "Please verify your email address before making purchases.")
        return redirect('karkahan:factory_list')
    
    messages.warning(request, "Please use the new checkout system for better experience.")
    return redirect('karkahan:cart_view')


@login_required
def process_payment(request):
    """Legacy payment processing (deprecated)"""
    # Check if user can make purchases (email verification)
    if not can_make_purchase(request.user):
        messages.error(request, "Please verify your email address before making payments.")
        return redirect('karkahan:factory_list')
    
    messages.warning(request, "Please use the new payment system for better experience.")
    return redirect('karkahan:cart_view')


@login_required
def payment_success(request):
    """Legacy payment success page (deprecated)"""
    # Get the latest completed purchases for this user
    recent_purchases = FactoryPurchase.objects.filter(
        user=request.user,
        payment_status='completed'
    ).order_by('-created_at')[:5]
    
    total_spent = sum(purchase.total_amount for purchase in recent_purchases)
    
    context = {
        'recent_purchases': recent_purchases,
        'total_spent': total_spent,
        'purchase_count': recent_purchases.count(),
    }
    return render(request, 'karkahan/payment_success.html', context)


@login_required
def payment_failure(request):
    """Legacy payment failure page (deprecated)"""
    # Get pending purchases that failed
    pending_purchases = FactoryPurchase.objects.filter(
        user=request.user,
        payment_status='pending'
    )
    
    context = {
        'pending_purchases': pending_purchases,
        'retry_available': pending_purchases.exists(),
    }
    return render(request, 'karkahan/payment_failure.html', context)


@login_required
def purchase_history(request):
    """View user's purchase history (legacy)"""
    purchases = PurchaseHistory.objects.filter(user=request.user).order_by('-purchase_date')
    
    context = {
        'purchases': purchases,
    }
    return render(request, 'karkahan/purchase_history.html', context)


@login_required
def resend_purchase_email(request, purchase_id):
    """Resend factory details email for a specific purchase (legacy)"""
    purchase = get_object_or_404(
        FactoryPurchase, 
        id=purchase_id, 
        user=request.user,
        payment_status='completed'
    )
    
    if purchase.email_sent:
        messages.info(request, "Email has already been sent for this purchase.")
    else:
        purchase.send_factory_details_email()
        messages.success(request, "Factory details email has been sent to your registered email address.")
    
    return redirect('karkahan:purchase_history')


@login_required
def send_selected_emails(request):
    """Send emails for selected purchases using centralized email service"""
    if request.method == 'POST':
        selected_purchase_ids = request.POST.getlist('selected_purchases')
        
        if not selected_purchase_ids:
            messages.warning(request, "Please select at least one purchase to send email for.")
            return redirect('karkahan:purchase_history')
        
        # Get the selected purchases
        purchases = FactoryPurchase.objects.filter(
            id__in=selected_purchase_ids,
            user=request.user,
            payment_status='completed'
        )
        
        if not purchases.exists():
            messages.error(request, "No valid purchases found.")
            return redirect('karkahan:purchase_history')
        
        # Filter out already sent emails
        unsent_purchases = purchases.filter(email_sent=False)
        already_sent_count = purchases.count() - unsent_purchases.count()
        
        if not unsent_purchases.exists():
            messages.info(request, "All selected purchases already have emails sent.")
            return redirect('karkahan:purchase_history')
        
        # Send emails for multiple factories using centralized service
        sent_count = 0
        try:
            # Use centralized email service to send bulk email
            success = FactoryEmailService.send_bulk_factory_emails(
                user_email=request.user.email,
                user_name=request.user.username,
                factories=[purchase.factory for purchase in unsent_purchases]
            )
            
            if success:
                # Update all purchases as sent
                current_time = timezone.now()
                for purchase in unsent_purchases:
                    purchase.email_sent = True
                    purchase.email_sent_at = current_time
                    purchase.save()
                    
                    # Update corresponding PurchaseHistory record
                    try:
                        purchase_history = PurchaseHistory.objects.filter(
                            user=purchase.user,
                            factory_slug=purchase.factory.slug,
                            purchase_date=purchase.purchased_at
                        ).first()
                        
                        if purchase_history:
                            purchase_history.email_delivered = True
                            purchase_history.email_delivered_at = current_time
                            purchase_history.save()
                    except Exception as history_error:
                        print(f"⚠️  Warning: Could not update PurchaseHistory record: {history_error}")
                
                sent_count = unsent_purchases.count()
            else:
                messages.error(request, "Failed to send emails. Please try again later.")
                return redirect('karkahan:purchase_history')
                
        except Exception as e:
            # Log detailed error information
            import traceback
            error_msg = f"❌ Failed to send bulk email: {str(e)}"
            error_details = f"Error details: {traceback.format_exc()}"
            print(error_msg)
            print(error_details)
            
            # Also log to Django's logging system
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Bulk email sending failed: {str(e)}")
            logger.error(f"User: {request.user.email}, Error details: {traceback.format_exc()}")
            
            messages.error(request, "Failed to send emails. Please try again later.")
            return redirect('karkahan:purchase_history')
        
        # Show success message
        if sent_count > 0:
            messages.success(request, f"Successfully sent factory details email for {sent_count} factory(ies) to {request.user.email}")
        
        if already_sent_count > 0:
            messages.info(request, f"{already_sent_count} selected purchase(s) already had emails sent.")
    
    return redirect('karkahan:purchase_history')


# Factory Detail with Purchase Logic
def factory_detail(request, slug):
    """Display factory details with purchase options"""
    factory = get_object_or_404(Factory, slug=slug, is_active=True, is_deleted=False)
    
    # Check if user has purchased this factory
    has_purchased = factory.has_user_purchased(request.user) if request.user.is_authenticated else False
    
    # Get related factories (same category, excluding current factory)
    related_factories = Factory.objects.filter(
        category=factory.category,
        is_active=True,
        is_deleted=False
    ).exclude(slug=factory.slug).order_by('?')[:3]
    
    context = {
        'factory': factory,
        'related_factories': related_factories,
        'has_purchased': has_purchased,
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


@login_required
def email_verification_help(request):
    """Help page for email verification"""
    verification_status = get_email_verification_message(request.user)
    
    context = {
        'verification_status': verification_status,
        'user_email': request.user.email,
        'is_verified': can_make_purchase(request.user),
        'help_text': """
            <h4>How to Verify Your Email Address</h4>
            <ol>
                <li><strong>Check Your Inbox:</strong> Look for an email from Factory InfoHub with the subject "Verify Your Email Address"</li>
                <li><strong>Click the Verification Link:</strong> Open the email and click the verification link provided</li>
                <li><strong>Confirmation:</strong> You will be redirected to a confirmation page</li>
                <li><strong>Start Shopping:</strong> Once verified, you can add items to cart and make purchases</li>
            </ol>
            
            <h4>Didn't Receive the Email?</h4>
            <ul>
                <li>Check your spam/junk folder</li>
                <li>Make sure you're checking the email address: <strong>{email}</strong></li>
                <li>Wait a few minutes - emails may take some time to arrive</li>
                <li>Contact support if you still haven't received it</li>
            </ul>
            
            <h4>Need Help?</h4>
            <p>If you're having trouble with email verification, please contact our support team at support@factoryinfohub.com</p>
        """.format(email=request.user.email)
    }
    return render(request, 'karkahan/email_verification_help.html', context)
