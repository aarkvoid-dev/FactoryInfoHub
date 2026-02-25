from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.http import HttpResponse
import csv
from django.contrib.auth.models import User
from Workers.models import Worker, WorkExperience
from Karkahan.models import Factory, FactoryImage
from category.models import Category, SubCategory
from location.models import Country, State, City, District, Region
from blog.models import BlogPost, BlogImage
from Accounts.models import Profile
from Home.models import ContactMessage
from .forms import AdminUserForm, AdminFactoryForm, AdminWorkerForm, AdminBlogForm, AdminBlogImageForm, AdminLocationForm, AdminCategoryForm, AdminCountryForm, AdminStateForm, AdminCityForm, AdminDistrictForm, AdminRegionForm, AdminSubCategoryForm, AdminFAQQuestionForm
from faq.models import FAQQuestion

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
    report_count = 0  # TODO: Implement report counting

    # Get today's counts
    today = datetime.now().date()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_factories_today = Factory.objects.filter(created_at__date=today).count()
    new_workers_today = Worker.objects.filter(created_at__date=today).count()
    reports_today = 0  # TODO: Implement report counting

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
            'timestamp': user.date_joined
        })

    # Add factory creation activities
    recent_factory_creations = Factory.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]

    for factory in recent_factory_creations:
        recent_activities.append({
            'type': 'factory_created',
            'message': f'Factory {factory.name} created',
            'timestamp': factory.created_at
        })

    # Add worker creation activities
    recent_worker_creations = Worker.objects.filter(
        created_at__gte=today - timedelta(days=7)
    ).order_by('-created_at')[:5]

    for worker in recent_worker_creations:
        recent_activities.append({
            'type': 'worker_created',
            'message': f'Worker {worker.full_name} created',
            'timestamp': worker.created_at
        })

    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = recent_activities[:10]

    context = {
        'user_count': user_count,
        'factory_count': factory_count,
        'worker_count': worker_count,
        'report_count': report_count,
        'new_users_today': new_users_today,
        'new_factories_today': new_factories_today,
        'new_workers_today': new_workers_today,
        'reports_today': reports_today,
        'recent_activities': recent_activities,
    }

    return render(request, 'CustomAdmin/dashboard/dashboard.html', context)

@login_required
def admin_users(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    users = User.objects.all()
    return render(request, 'CustomAdmin/users/users.html', {'users': users})

@login_required
def admin_user_edit(request, user_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Handle user update logic here
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_active = 'is_active' in request.POST
        
        # Update role if provided
        new_role = request.POST.get('role')
        if new_role in ['admin', 'staff', 'user']:
            user.profile.role = new_role
        
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
def admin_factories(request):
    profile = request.user.profile
    if profile.role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    f_country = request.GET.get('country')
    f_state = request.GET.get('state')
    f_city = request.GET.get('city')
    f_district = request.GET.get('distric') # Matching your HTML spelling
    f_region = request.GET.get('region')
    f_category = request.GET.get('category')
    f_subcategory = request.GET.get('subcategory')
    f_search = request.GET.get('search', '')
    f_status = request.GET.get('status')
    f_deleted = request.GET.get('deleted', 'active')  # 'active', 'deleted', 'all'

    # 2. Build Factory Queryset
    factories = Factory.objects.all_with_deleted().select_related('category', 'subcategory', 'country', 'state', 'city', 'district', 'region')

    if f_country: factories = factories.filter(country_id=f_country)
    if f_state: factories = factories.filter(state_id=f_state)
    if f_city: factories = factories.filter(city_id=f_city)
    if f_district: factories = factories.filter(district_id=f_district)
    if f_region: factories = factories.filter(region_id=f_region)
    if f_category: factories = factories.filter(category_id=f_category)
    if f_subcategory: factories = factories.filter(subcategory_id=f_subcategory)
    if f_search: factories = factories.filter(name__icontains=f_search)
    
    if f_status == 'active':
        factories = factories.filter(is_active=True)
    elif f_status == 'inactive':
        factories = factories.filter(is_active=False)

    # Filter by deleted status
    if f_deleted == 'deleted':
        factories = factories.filter(is_deleted=True)
    elif f_deleted == 'active':
        factories = factories.filter(is_deleted=False)

    # 3. CSV Export
    if 'download' in request.GET:
        return export_factories_to_csv(factories)

    # 4. PERSISTENT DROPDOWNS: Fetch options based on current selections
    countries = Country.objects.filter(is_deleted=False)
    categories = Category.objects.filter(is_deleted=False)
    
    # Only fetch children if parent is selected
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

    # 1. Capture Filter Parameters
    category_id = request.GET.get('category')
    subcategory_id = request.GET.get('subcategory')
    experience_min = request.GET.get('experience_min')
    experience_max = request.GET.get('experience_max')
    status = request.GET.get('status')
    gender = request.GET.get('gender')
    availability = request.GET.get('availability')
    
    # Location Parameters
    country_id = request.GET.get('country')
    state_id = request.GET.get('state')
    city_id = request.GET.get('city')
    district_id = request.GET.get('district')
    region_id = request.GET.get('region') # Added Region support
    
    deleted_view = request.GET.get('deleted', 'active')

    # 2. Queryset Optimization
    # Added 'district' and 'region' to select_related for speed
    workers = Worker.objects.all().select_related(
        'category', 'subcategory', 'country', 'state', 'city', 'district', 'region'
    )

    # 3. Soft Delete Logic
    if deleted_view == 'deleted':
        workers = Worker.objects.all_with_deleted().filter(is_deleted=True)
    elif deleted_view == 'all':
        workers = Worker.objects.all_with_deleted()
    else:
        workers = workers.filter(is_deleted=False)

    # 4. Apply Filters (using the captured IDs)
    if category_id: workers = workers.filter(category_id=category_id)
    if subcategory_id: workers = workers.filter(subcategory_id=subcategory_id)
    if country_id: workers = workers.filter(country_id=country_id)
    if state_id: workers = workers.filter(state_id=state_id)
    if city_id: workers = workers.filter(city_id=city_id)
    if district_id: workers = workers.filter(district_id=district_id)
    if region_id: workers = workers.filter(region_id=region_id) # Filter by Region

    if gender: workers = workers.filter(gender=gender)
    if availability: workers = workers.filter(availability=availability)
    
    if experience_min: workers = workers.filter(years_of_experience__gte=experience_min)
    if experience_max: workers = workers.filter(years_of_experience__lte=experience_max)

    if status == 'active':
        workers = workers.filter(is_active=True)
    elif status == 'inactive':
        workers = workers.filter(is_active=False)

    # 5. CSV Export
    if 'download' in request.GET:
        return export_workers_to_csv(workers)

    # 6. Optimized Context
    # We remove 'cities', 'states', etc. from context because JS loads them.
    # This makes the initial page load much lighter.
    context = {
        'workers': workers,
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
        }
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
            worker = form.save()
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
        'worker': worker
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
    
    if request.method == 'POST':
        form = AdminCountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(request, f'Country "{country.name}" created successfully!')
            return redirect('admin_interface:admin_countries')
    else:
        form = AdminCountryForm()

    return render(request, 'CustomAdmin/locations/countries.html', {
        'countries': countries,
        'form': form,
        'location_type': 'Country'
    })

@login_required
def admin_states(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    states = State.objects.filter(is_deleted=False)
    
    if request.method == 'POST':
        form = AdminStateForm(request.POST)
        if form.is_valid():
            state = form.save()
            messages.success(request, f'State "{state.name}" created successfully!')
            return redirect('admin_interface:admin_states')
    else:
        form = AdminStateForm()

    return render(request, 'CustomAdmin/locations/states.html', {
        'states': states,
        'form': form,
        'location_type': 'State'
    })

@login_required
def admin_cities(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    cities = City.objects.filter(is_deleted=False)
    
    if request.method == 'POST':
        form = AdminCityForm(request.POST)
        if form.is_valid():
            city = form.save()
            messages.success(request, f'City "{city.name}" created successfully!')
            return redirect('admin_interface:admin_cities')
    else:
        form = AdminCityForm()

    return render(request, 'CustomAdmin/locations/cities.html', {
        'cities': cities,
        'form': form,
        'location_type': 'City'
    })

@login_required
def admin_districts(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    districts = District.objects.filter(is_deleted=False)
    
    if request.method == 'POST':
        form = AdminDistrictForm(request.POST)
        if form.is_valid():
            district = form.save()
            messages.success(request, f'District "{district.name}" created successfully!')
            return redirect('admin_interface:admin_districts')
    else:
        form = AdminDistrictForm()

    return render(request, 'CustomAdmin/locations/districts.html', {
        'districts': districts,
        'form': form,
        'location_type': 'District'
    })

@login_required
def admin_regions(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    regions = Region.objects.filter(is_deleted=False)
    
    if request.method == 'POST':
        form = AdminRegionForm(request.POST)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region "{region.name}" created successfully!')
            return redirect('admin_interface:admin_regions')
    else:
        form = AdminRegionForm()

    return render(request, 'CustomAdmin/locations/regions.html', {
        'regions': regions,
        'form': form,
        'location_type': 'Region'
    })

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
        form = AdminCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_interface:admin_categories')
    else:
        form = AdminCategoryForm()

    return render(request, 'CustomAdmin/locations/categories.html', {
        'categories': categories,
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

    subcategories = SubCategory.objects.filter(is_deleted=False)
    
    if request.method == 'POST':
        form = AdminSubCategoryForm(request.POST)
        if form.is_valid():
            subcategory = form.save()
            messages.success(request, f'Subcategory "{subcategory.name}" created successfully!')
            return redirect('admin_interface:admin_subcategories')
    else:
        form = AdminSubCategoryForm()

    return render(request, 'CustomAdmin/locations/subcategories.html', {
        'subcategories': subcategories,
        'form': form,
        'category_type': 'Subcategory'
    })

def export_factories_to_csv(factories):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="factories.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Category', 'Sub Category', 'Location', 'Capacity', 'Owner', 'Status'])

    for factory in factories:
        owner = ', '.join([profile.user.username for profile in factory.profiles.all()]) if factory.profiles.exists() else 'No owner'
        location = f"{factory.city.name}, {factory.state.name}, {factory.country.name}"
        writer.writerow([
            factory.id,
            factory.name,
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
    writer.writerow(['ID', 'Name', 'Category', 'Position', 'Factory', 'Experience', 'Age', 'Gender', 'Status'])

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
        writer.writerow(['ID', 'Name', 'Category', 'Sub Category', 'Location', 'Capacity', 'Owner', 'Created At'])

        for factory in factories:
            owner = ', '.join([profile.user.username for profile in factory.profiles.all()]) if factory.profiles.exists() else 'No owner'
            location = f"{factory.city.name}, {factory.state.name}, {factory.country.name}"
            writer.writerow([
                factory.id,
                factory.name,
                factory.category.name,
                factory.subcategory.name if factory.subcategory else 'N/A',
                location,
                factory.capacity,
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
        writer.writerow(['ID', 'Name', 'Category', 'Position', 'Factory', 'Experience', 'Age', 'Gender', 'Created At'])

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
                worker.position,
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
        writer.writerow(['Type', 'ID', 'Name', 'Category', 'Details', 'Created At'])

        factories = Factory.objects.filter(created_at__range=[start_date, end_date])
        workers = Worker.objects.filter(created_at__range=[start_date, end_date])

        for factory in factories:
            location = f"{factory.city.name}, {factory.state.name}, {factory.country.name}"
            writer.writerow([
                'Factory',
                factory.id,
                factory.name,
                factory.category.name,
                location,
                factory.created_at,
            ])

        for worker in workers:
            writer.writerow([
                'Worker',
                worker.id,
                worker.full_name,
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
    
    if request.method == 'POST':
        form = AdminFactoryForm(request.POST, request.FILES, instance=factory)
        if form.is_valid():
            factory = form.save()
            messages.success(request, f'Factory "{factory.name}" updated successfully!')
            return redirect('admin_interface:admin_factories')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminFactoryForm(instance=factory)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit Factory: {factory.name}',
        'factory': factory
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
def admin_factory_detail(request, factory_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    factory = get_object_or_404(Factory, id=factory_id)
    images = factory.images.all()

    context = {
        'factory': factory,
        'images': images,
        'title': f'Factory Details: {factory.name}'
    }
    return render(request, 'CustomAdmin/factories/factory_detail.html', context)

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

# FAQ CRUD Views
@login_required
def admin_faq(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    f_category = request.GET.get('category')
    f_status = request.GET.get('status')
    f_search = request.GET.get('search', '')
    f_deleted = request.GET.get('deleted', 'active')  # 'active', 'deleted', 'all'

    # 2. Build Queryset
    questions = FAQQuestion.objects.all_with_deleted().select_related('category')

    if f_category: questions = questions.filter(category_id=f_category)
    if f_search: questions = questions.filter(
        Q(title__icontains=f_search) | Q(question_text__icontains=f_search) | Q(answer_text__icontains=f_search)
    )
    
    if f_status == 'published':
        questions = questions.filter(is_published=True)
    elif f_status == 'draft':
        questions = questions.filter(is_published=False)

    # Filter by deleted status
    if f_deleted == 'deleted':
        questions = questions.filter(is_deleted=True)
    elif f_deleted == 'active':
        questions = questions.filter(is_deleted=False)

    # 3. Persistent Dropdowns
    categories = Category.objects.filter(is_deleted=False)

    context = {
        'questions': questions,
        'categories': categories,
        'filters': {
            'category': f_category,
            'status': f_status,
            'search': f_search,
            'deleted': f_deleted,
        }
    }
    return render(request, 'CustomAdmin/faq/faq.html', context)

@login_required
def admin_faq_create(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    if request.method == 'POST':
        form = AdminFAQQuestionForm(request.POST)
        if form.is_valid():
            question = form.save()
            messages.success(request, f'FAQ question "{question.title}" created successfully!')
            return redirect('admin_interface:admin_faq')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminFAQQuestionForm()

    context = {
        'form': form,
        'action': 'create',
        'title': 'Create New FAQ Question'
    }
    return render(request, 'CustomAdmin/faq/faq_form.html', context)

@login_required
def admin_faq_edit(request, question_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    question = get_object_or_404(FAQQuestion, id=question_id, is_deleted=False)
    
    if request.method == 'POST':
        form = AdminFAQQuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            messages.success(request, f'FAQ question "{question.title}" updated successfully!')
            return redirect('admin_interface:admin_faq')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AdminFAQQuestionForm(instance=question)

    context = {
        'form': form,
        'action': 'edit',
        'title': f'Edit FAQ Question: {question.title}',
        'question': question
    }
    return render(request, 'CustomAdmin/faq/faq_form.html', context)

@login_required
def admin_faq_delete(request, question_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    question = get_object_or_404(FAQQuestion, id=question_id, is_deleted=False)
    
    if request.method == 'POST':
        question_title = question.title
        question.delete()
        messages.success(request, f'FAQ question "{question_title}" deleted successfully!')
        return redirect('admin_interface:admin_faq')

    context = {
        'question': question,
        'title': f'Delete FAQ Question: {question.title}'
    }
    return render(request, 'CustomAdmin/faq/faq_delete.html', context)

@login_required
def admin_faq_restore(request, question_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    question = get_object_or_404(FAQQuestion.objects.all_with_deleted(), id=question_id)
    
    if request.method == 'POST':
        question_title = question.title
        question.restore()
        messages.success(request, f'FAQ question "{question_title}" restored successfully!')
        return redirect('admin_interface:admin_faq')

    context = {
        'question': question,
        'title': f'Restore FAQ Question: {question.title}'
    }
    return render(request, 'CustomAdmin/faq/faq_restore.html', context)

@login_required
def admin_faq_detail(request, question_id):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    question = get_object_or_404(FAQQuestion, id=question_id, is_deleted=False)

    context = {
        'question': question,
        'title': f'FAQ Question Details: {question.title}'
    }
    return render(request, 'CustomAdmin/faq/faq_detail.html', context)

@login_required
def admin_contacts(request):
    profile = request.user.profile
    role = profile.role

    if role not in ['admin', 'staff'] and not (request.user.is_staff or request.user.is_superuser):
        return render(request, 'CustomAdmin/permission_denied.html')

    # 1. Capture Filter Parameters
    search = request.GET.get('search', '')
    status = request.GET.get('status')
    user_id = request.GET.get('user')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    deleted_view = request.GET.get('deleted', 'active')

    # 2. Build Queryset
    messages = ContactMessage.objects.all_with_deleted().select_related('user')

    # Apply filters
    if search:
        messages = messages.filter(
            Q(name__icontains=search) | 
            Q(email__icontains=search) | 
            Q(subject__icontains=search) | 
            Q(message__icontains=search)
        )
    
    if status == 'unread':
        messages = messages.filter(is_read=False)
    elif status == 'read':
        messages = messages.filter(is_read=True)
    
    if user_id:
        messages = messages.filter(user_id=user_id)
    
    if start_date:
        messages = messages.filter(created_at__date__gte=start_date)
    
    if end_date:
        messages = messages.filter(created_at__date__lte=end_date)

    # Filter by deleted status
    if deleted_view == 'deleted':
        messages = messages.filter(is_deleted=True)
    elif deleted_view == 'active':
        messages = messages.filter(is_deleted=False)

    # 3. Calculate Summary Statistics
    total_count = messages.count()
    unread_count = messages.filter(is_read=False).count()
    read_count = messages.filter(is_read=True).count()
    
    # Count messages from this month
    from datetime import date
    first_day_of_month = date.today().replace(day=1)
    this_month_count = messages.filter(created_at__date__gte=first_day_of_month).count()

    # 4. CSV Export
    if 'download' in request.GET:
        return export_contact_messages_to_csv(messages)

    # 5. Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(messages, 20)  # Show 20 messages per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # 6. Get Users for Filter Dropdown
    users = User.objects.filter(contactmessage__isnull=False).distinct()

    context = {
        'messages': page_obj,
        'users': users,
        'unread_count': unread_count,
        'read_count': read_count,
        'this_month_count': this_month_count,
        'filters': {
            'search': search,
            'status': status,
            'user': user_id,
            'start_date': start_date,
            'end_date': end_date,
            'deleted': deleted_view,
        }
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
        return render(request, 'CustomAdmin/permission_denied.html')

    message = get_object_or_404(ContactMessage, id=message_id)
    
    if request.method == 'POST':
        message_name = message.name
        message.delete()
        messages.success(request, f'Message from {message_name} deleted successfully.')
        return redirect('admin_interface:admin_contacts')

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

def export_contact_messages_to_csv(messages):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="contact_messages.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Email', 'Subject', 'Message', 'User', 'Status', 'Created At', 'Read At'])

    for message in messages:
        writer.writerow([
            message.id,
            message.name,
            message.email,
            message.subject,
            message.message.replace('\n', ' ').replace('\r', ''),
            message.user.username if message.user else 'Guest',
            'Read' if message.is_read else 'Unread',
            message.created_at,
            message.read_at if message.read_at else '',
        ])

    return response


