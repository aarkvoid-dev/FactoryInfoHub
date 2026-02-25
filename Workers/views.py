from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Worker, WorkExperience
from .forms import WorkerForm, WorkExperienceForm, WorkerFilterForm, WorkerProfileForm

def register_worker(request):
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            worker = form.save()
            messages.success(request, f'Worker "{worker.full_name}" has been registered successfully!')
            return redirect('workers:worker_detail', slug=worker.slug)
    else:
        form = WorkerForm()
    return render(request, 'workers/register.html', {'form': form, 'title': 'Register as Worker'})

@login_required
def worker_profile(request):
    worker = get_object_or_404(Worker, user=request.user)
    return render(request, 'workers/profile.html', {'worker': worker})

def edit_worker_profile(request, slug):
    worker = get_object_or_404(Worker, slug=slug)
    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('workers:worker_detail', slug=worker.slug)
    else:
        form = WorkerProfileForm(instance=worker)
    return render(request, 'workers/edit_profile.html', {'form': form, 'worker': worker})

@login_required
def add_work_experience(request):
    worker = get_object_or_404(Worker, user=request.user)
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST)
        if form.is_valid():
            experience = form.save(commit=False)
            experience.worker = worker
            experience.save()
            messages.success(request, 'Work experience added successfully!')
            return redirect('workers:worker_profile')
    else:
        form = WorkExperienceForm()
    return render(request, 'workers/add_experience.html', {'form': form})

@login_required
def edit_work_experience(request, experience_id):
    experience = get_object_or_404(WorkExperience, id=experience_id, worker__user=request.user)
    if request.method == 'POST':
        form = WorkExperienceForm(request.POST, instance=experience)
        if form.is_valid():
            form.save()
            messages.success(request, 'Work experience updated successfully!')
            return redirect('workers:worker_profile')
    else:
        form = WorkExperienceForm(instance=experience)
    return render(request, 'workers/edit_experience.html', {'form': form, 'experience': experience})

@login_required
def delete_work_experience(request, experience_id):
    experience = get_object_or_404(WorkExperience, id=experience_id, worker__user=request.user)
    experience.delete()
    messages.success(request, 'Work experience deleted successfully!')
    return redirect('workers:worker_profile')

def worker_list(request):
    """List all workers with filtering and search"""
    workers = Worker.objects.filter(is_active=True, is_deleted=False).select_related(
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
    filter_form = WorkerFilterForm(request.GET, initial=initial_data)
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        subcategory = filter_form.cleaned_data.get('subcategory')
        country = filter_form.cleaned_data.get('country')
        state = filter_form.cleaned_data.get('state')
        city = filter_form.cleaned_data.get('city')
        district = filter_form.cleaned_data.get('district')
        region = filter_form.cleaned_data.get('region')
        availability = filter_form.cleaned_data.get('availability')
        min_experience = filter_form.cleaned_data.get('min_experience')
        max_wage = filter_form.cleaned_data.get('max_wage')

        if category:
            workers = workers.filter(category=category)
        if subcategory:
            workers = workers.filter(subcategory=subcategory)
        if country:
            workers = workers.filter(country=country)
        if state:
            workers = workers.filter(state=state)
        if city:
            workers = workers.filter(city=city)
        if district:
            workers = workers.filter(district=district)
        if region:
            workers = workers.filter(region=region)
        if availability:
            workers = workers.filter(availability=availability)
        if min_experience:
            workers = workers.filter(years_of_experience__gte=min_experience)
        if max_wage:
            workers = workers.filter(expected_daily_wage__lte=max_wage)

    # Apply search
    search_query = request.GET.get('q', '')
    if search_query:
        workers = workers.filter(
            Q(full_name__icontains=search_query) |
            Q(skills__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(subcategory__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(workers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'search_query': search_query,
    }
    return render(request, 'workers/worker_list.html', context)

def worker_detail(request, slug):
    worker = get_object_or_404(Worker, slug=slug)
    experiences = worker.experiences.all()
    skill_list = [s.strip() for s in worker.skills.split(',')] if worker.skills else []
    return render(request, 'workers/worker_detail.html', {
        'worker': worker,
        'skill_list': skill_list,
        'experiences': experiences
    })
