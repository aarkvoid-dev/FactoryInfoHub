from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import login
from django.urls import reverse
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import Factory, ShoppingCart, FactoryPurchase, PurchaseHistory
from .forms import FactoryForm, FactoryFilterForm, FactoryImageFormSet
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region


def factory_list(request):
    """List all factories with filtering and search"""
    factories = Factory.objects.filter(is_active=True, is_deleted=False).select_related(
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


@login_required
def factory_create(request):
    """Create a new factory"""
    if request.method == 'POST':
        form = FactoryForm(request.POST)
        formset = FactoryImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            from django.db import transaction
            
            try:
                with transaction.atomic():
                    # 1. Save factory details
                    factory = form.save()
                    
                    # 2. Link and save images
                    formset.instance = factory
                    formset.save()
                    
                    # 3. Logic to set default primary image
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
        form = FactoryForm(request.POST, instance=factory)
        # Add prefix='images' here!
        formset = FactoryImageFormSet(request.POST, request.FILES, instance=factory, prefix='images')
        print("FactoryForm : ",form.errors,"formset :",formset.errors)
        if form.is_valid() and formset.is_valid():
            factory = form.save()
            formset.save()
            
            # Ensure only one image is primary
            primary_count = factory.images.filter(is_primary=True).count()
            if primary_count == 0 and factory.images.exists():
                # Set first image as primary if none is set
                first_image = factory.images.first()
                first_image.is_primary = True
                first_image.save()
            elif primary_count > 1:
                # If multiple images are marked as primary, keep only the first one
                primary_images = factory.images.filter(is_primary=True)
                first_primary = primary_images.first()
                primary_images.exclude(pk=first_primary.pk).update(is_primary=False)
            
            messages.success(request, f'Factory "{factory.name}" updated!')
            return redirect('karkahan:factory_detail', slug=factory.slug)
    else:
        form = FactoryForm(instance=factory)
        # Add prefix='images' here too!
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


# Shopping Cart Views
@login_required
def add_to_cart(request, factory_slug):
    """Add a factory to the shopping cart"""
    factory = get_object_or_404(Factory, slug=factory_slug, is_active=True, is_deleted=False)
    
    # Check if already purchased
    # if factory.has_user_purchased(request.user):
    #     messages.warning(request, 'You have already purchased this factory.')
    #     return redirect('karkahan:factory_detail', slug=factory_slug)
    
    # Check if already in cart - if so, just show message (no quantity increase)
    cart_item, created = ShoppingCart.objects.get_or_create(
        user=request.user,
        factory=factory,
        defaults={'quantity': 1}
    )
    
    if not created:
        messages.info(request, f'{factory.name} is already in your cart.')
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
def update_cart_quantity(request, cart_item_id):
    """Update quantity of an item in the cart"""
    if request.method == 'POST':
        cart_item = get_object_or_404(ShoppingCart, id=cart_item_id, user=request.user)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            cart_item.delete()
            messages.success(request, f"Item removed from cart.")
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, f"Quantity updated for {cart_item.factory.name}.")
    
    return redirect('karkahan:cart_view')


@login_required
def cart_view(request):
    """View the shopping cart"""
    cart_items = ShoppingCart.objects.filter(user=request.user).select_related('factory')
    total_price = ShoppingCart.get_cart_total(request.user)
    cart_count = ShoppingCart.get_cart_count(request.user)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
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


# Checkout and Purchase Views
@login_required
def checkout(request):
    """Checkout page to review and complete purchase"""
    cart_items = ShoppingCart.objects.filter(user=request.user).select_related('factory')
    
    if not cart_items.exists():
        messages.info(request, "Your cart is empty.")
        return redirect('karkahan:factory_list')
    
    total_price = ShoppingCart.get_cart_total(request.user)
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'karkahan/checkout.html', context)


@login_required
def process_purchase(request):
    """Process the purchase and create FactoryPurchase records"""
    if request.method == 'POST':
        cart_items = ShoppingCart.objects.filter(user=request.user).select_related('factory')
        
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('karkahan:cart_view')
        
        total_amount = 0
        
        # Create purchase records in a transaction
        with transaction.atomic():
            for cart_item in cart_items:
                factory = cart_item.factory
                
                # Create FactoryPurchase record
                purchase = FactoryPurchase.objects.create(
                    user=request.user,
                    factory=factory,
                    quantity=cart_item.quantity,
                    price_at_purchase=factory.price,
                    payment_status='pending',
                    transaction_id=f"FACTORY_{factory.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
                )
                
                total_amount += purchase.total_amount
                
                # Create PurchaseHistory record
                PurchaseHistory.create_from_purchase(purchase)
        
        # Clear the cart
        cart_items.delete()
        
        # Redirect to payment page - convert Decimal to int for URL
        purchase_amount_int = int(total_amount)
        messages.success(request, f"Purchase created successfully! Total amount: Rs. {total_amount}")
        return redirect('karkahan:payment_page', purchase_amount=purchase_amount_int)
    
    return redirect('karkahan:checkout')


@login_required
def payment_page(request, purchase_amount):
    """Proxy payment page for demonstration"""
    context = {
        'amount': purchase_amount,
        'formatted_amount': f"Rs. {purchase_amount:,}",
    }
    return render(request, 'karkahan/payment.html', context)


@login_required
def process_payment(request):
    """Process the proxy payment"""
    if request.method == 'POST':
        # Simulate payment processing
        amount = request.POST.get('amount', '0')
        
        try:
            amount = float(amount.replace(',', '').replace('Rs.', '').strip())
        except ValueError:
            messages.error(request, "Invalid amount.")
            return redirect('karkahan:payment_page', purchase_amount=0)
        
        # Get pending purchases for this user
        pending_purchases = FactoryPurchase.objects.filter(
            user=request.user,
            payment_status='pending'
        )
        
        if not pending_purchases.exists():
            messages.error(request, "No pending purchases found.")
            return redirect('karkahan:factory_list')
        
        # Calculate total amount from purchases to verify
        total_amount = sum(purchase.total_amount for purchase in pending_purchases)
        
        # Verify amount matches
        if abs(float(amount) - float(total_amount)) > 0.01:  # Small tolerance for floating point
            messages.error(request, f"Amount mismatch. Expected: Rs. {total_amount}, Got: Rs. {amount}")
            return redirect('karkahan:payment_page', purchase_amount=int(total_amount))
        
        # Mark purchases as completed in a transaction
        try:
            with transaction.atomic():
                for purchase in pending_purchases:
                    purchase.mark_as_completed()
            
            messages.success(request, "Payment completed successfully! Factory details have been sent to your email.")
            return redirect('karkahan:payment_success')
            
        except Exception as e:
            messages.error(request, f"Payment processing failed: {str(e)}")
            return redirect('karkahan:payment_failure')
    
    return redirect('karkahan:payment_page', purchase_amount=0)


@login_required
def payment_success(request):
    """Payment success page"""
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
    """Payment failure page"""
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
    """View user's purchase history"""
    purchases = PurchaseHistory.objects.filter(user=request.user).order_by('-purchase_date')
    
    context = {
        'purchases': purchases,
    }
    return render(request, 'karkahan/purchase_history.html', context)


@login_required
def resend_purchase_email(request, purchase_id):
    """Resend factory details email for a specific purchase"""
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
    """Send emails for selected purchases"""
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
        
        # Send emails for multiple factories
        sent_count = 0
        try:
            # Create a combined email for multiple factories
            subject = f"Factory Details - {unsent_purchases.count()} Factory(ies)"
            message = f"""
            Dear {request.user.username},

            Thank you for your purchases! Here are the details for the factories you requested:

            """
            
            # Add details for each factory
            for i, purchase in enumerate(unsent_purchases, 1):
                factory = purchase.factory
                message += f"""
            ---
            Factory {i}: {factory.name}
            Category: {factory.category.name}
            Location: {factory.full_address}
            Type: {factory.factory_type}
            Production Capacity: {factory.production_capacity}
            Employee Count: {factory.employee_count}
            Established: {factory.established_year}
            Annual Turnover: {factory.annual_turnover}

            Contact Information:
            Contact Person: {factory.contact_person}
            Phone: {factory.contact_phone}
            Email: {factory.contact_email}
            Website: {factory.website}

            Address: {factory.address}
            {factory.city.name}, {factory.state.name} - {factory.pincode}
            {factory.country.name}

            """
            
            message += """
            This information is confidential and intended solely for your use.

            Best regards,
            Factory InfoHub Team
            """

            # Send email with SSL context that bypasses certificate verification
            import ssl
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            from django.conf import settings
            from django.utils import timezone
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.DEFAULT_FROM_EMAIL
            msg['To'] = request.user.email
            
            # Add text content
            text_part = MIMEText(message, 'plain')
            msg.attach(text_part)
            
            # Send email with SSL context that bypasses certificate verification
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
                if settings.EMAIL_USE_TLS:
                    server.starttls(context=context)
                if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                    server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
                server.send_message(msg)
            
            # Update all purchases as sent
            current_time = timezone.now()
            for purchase in unsent_purchases:
                purchase.email_sent = True
                purchase.email_sent_at = current_time
                purchase.save()
                
                # Update corresponding PurchaseHistory record
                try:
                    purchase_history = purchase_history = purchase_history = PurchaseHistory.objects.filter(
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