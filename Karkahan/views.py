from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Factory
from .forms import FactoryForm, FactoryFilterForm
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region


def factory_list(request):
    """List all factories with filtering and search"""
    factories = Factory.objects.filter(is_active=True, is_deleted=False).select_related(
        'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    )
    
    # Apply filters
    filter_form = FactoryFilterForm(request.GET)
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        subcategory = filter_form.cleaned_data.get('subcategory')
        country = filter_form.cleaned_data.get('country')
        state = filter_form.cleaned_data.get('state')
        city = filter_form.cleaned_data.get('city')
        factory_type = filter_form.cleaned_data.get('factory_type')
        is_active = filter_form.cleaned_data.get('is_active')

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
        if factory_type:
            factories = factories.filter(factory_type__icontains=factory_type)
        if is_active is not None:
            factories = factories.filter(is_active=is_active)

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

    # Sort
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


def factory_detail(request, slug):
    """Display factory details"""
    factory = get_object_or_404(Factory, slug=slug, is_active=True, is_deleted=False)
    
    # Get related factories (same category, excluding current factory)
    related_factories = Factory.objects.filter(
        category=factory.category,
        is_active=True,
        is_deleted=False
    ).exclude(slug=factory.slug).order_by('?')[:3]
    
    context = {
        'factory': factory,
        'related_factories': related_factories,
    }
    return render(request, 'karkahan/factory_detail.html', context)


@login_required
def factory_create(request):
    """Create a new factory"""
    if request.method == 'POST':
        form = FactoryForm(request.POST)
        if form.is_valid():
            factory = form.save()
            messages.success(request, f'Factory "{factory.name}" has been created successfully!')
            return redirect('karkahan:factory_detail', slug=factory.slug)
    else:
        form = FactoryForm()
    
    context = {
        'form': form,
        'title': 'Add New Factory',
    }
    return render(request, 'karkahan/factory_form.html', context)


@login_required
def factory_edit(request, slug):
    """Edit an existing factory"""
    factory = get_object_or_404(Factory, slug=slug, is_deleted=False)
    
    if request.method == 'POST':
        form = FactoryForm(request.POST, instance=factory)
        if form.is_valid():
            factory = form.save()
            messages.success(request, f'Factory "{factory.name}" has been updated successfully!')
            return redirect('karkahan:factory_detail', slug=factory.slug)
    else:
        form = FactoryForm(instance=factory)
    
    context = {
        'form': form,
        'factory': factory,
        'title': 'Edit Factory',
    }
    return render(request, 'karkahan/factory_form.html', context)


@login_required
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
def factory_toggle_active(request, slug):
    """Toggle factory active status"""
    factory = get_object_or_404(Factory, slug=slug, is_deleted=False)
    factory.is_active = not factory.is_active
    factory.save()
    
    status = "activated" if factory.is_active else "deactivated"
    messages.success(request, f'Factory "{factory.name}" has been {status} successfully!')
    return redirect('karkahan:factory_detail', slug=factory.slug)


@login_required
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