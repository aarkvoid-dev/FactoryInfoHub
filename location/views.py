from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count
from .models import Country, State, District, City, Region
from .forms import CountryForm, StateForm, DistrictForm, CityForm, RegionForm


@login_required
def location_dashboard(request):
    """Dashboard showing location management overview"""
    countries_count = Country.objects.count()
    states_count = State.objects.count()
    cities_count = City.objects.count()
    districts_count = District.objects.count()
    regions_count = Region.objects.count()

    # Calculate averages
    avg_states_per_country = round(states_count / countries_count, 1) if countries_count > 0 else 0
    avg_cities_per_state = round(cities_count / states_count, 1) if states_count > 0 else 0
    avg_districts_per_city = round(districts_count / cities_count, 1) if cities_count > 0 else 0
    total_locations = countries_count + states_count + cities_count + districts_count + regions_count

    context = {
        'countries_count': countries_count,
        'states_count': states_count,
        'districts_count': districts_count,
        'cities_count': cities_count,
        'regions_count': regions_count,
        'total_locations': total_locations,
        'avg_states_per_country': avg_states_per_country,
        'avg_cities_per_state': avg_cities_per_state,
        'avg_districts_per_city': avg_districts_per_city,
        'recent_countries': Country.objects.order_by('-created_at')[:5],
        'recent_states': State.objects.order_by('-created_at')[:5],
        'recent_cities': City.objects.order_by('-created_at')[:5],
    }
    return render(request, 'location/dashboard.html', context)


# Country Views
@login_required
def country_list(request):
    countries = Country.objects.all()
    return render(request, 'location/country_list.html', {'countries': countries})


@login_required
def country_detail(request, slug):
    country = get_object_or_404(Country, slug=slug)
    states = country.states.all()
    context = {
        'country': country,
        'states': states,
        'states_count': states.count(),
    }
    return render(request, 'location/country_detail.html', context)


@login_required
def country_create(request):
    if request.method == 'POST':
        form = CountryForm(request.POST)
        if form.is_valid():
            country = form.save()
            messages.success(request, f'Country "{country.name}" created successfully!')
            return redirect('location:country_detail', slug=country.slug)
    else:
        form = CountryForm()
    return render(request, 'location/country_form.html', {'form': form, 'title': 'Add Country'})


@login_required
def country_update(request, slug):
    country = get_object_or_404(Country, slug=slug)
    if request.method == 'POST':
        form = CountryForm(request.POST, instance=country)
        if form.is_valid():
            country = form.save()
            messages.success(request, f'Country "{country.name}" updated successfully!')
            return redirect('location:country_detail', slug=country.slug)
    else:
        form = CountryForm(instance=country)
    return render(request, 'location/country_form.html', {'form': form, 'title': 'Edit Country', 'country': country})


@login_required
def country_delete(request, slug):
    country = get_object_or_404(Country, slug=slug)
    if request.method == 'POST':
        country_name = country.name
        country.delete()
        messages.success(request, f'Country "{country_name}" deleted successfully!')
        return redirect('location:country_list')
    return render(request, 'location/country_confirm_delete.html', {'country': country})


# State Views
@login_required
def state_list(request):
    states = State.objects.select_related('country')
    return render(request, 'location/state_list.html', {'states': states})


@login_required
def state_detail(request, slug):
    state = get_object_or_404(State, slug=slug)
    cities = state.cities.all()
    context = {
        'state': state,
        'cities': cities,
        'cities_count': cities.count(),
    }
    return render(request, 'location/state_detail.html', context)


@login_required
def state_create(request):
    if request.method == 'POST':
        form = StateForm(request.POST)
        if form.is_valid():
            state = form.save()
            messages.success(request, f'State "{state.name}" created successfully!')
            return redirect('location:state_detail', slug=state.slug)
    else:
        form = StateForm()
    return render(request, 'location/state_form.html', {'form': form, 'title': 'Add State'})


@login_required
def state_update(request, slug):
    state = get_object_or_404(State, slug=slug)
    if request.method == 'POST':
        form = StateForm(request.POST, instance=state)
        if form.is_valid():
            state = form.save()
            messages.success(request, f'State "{state.name}" updated successfully!')
            return redirect('location:state_detail', slug=state.slug)
    else:
        form = StateForm(instance=state)
    return render(request, 'location/state_form.html', {'form': form, 'title': 'Edit State', 'state': state})


@login_required
def state_delete(request, slug):
    state = get_object_or_404(State, slug=slug)
    if request.method == 'POST':
        state_name = state.name
        state.delete()
        messages.success(request, f'State "{state_name}" deleted successfully!')
        return redirect('location:state_list')
    return render(request, 'location/state_confirm_delete.html', {'state': state})


# City Views
@login_required
def city_list(request):
    cities = City.objects.select_related('state__country')
    return render(request, 'location/city_list.html', {'cities': cities})


@login_required
def city_detail(request, slug):
    city = get_object_or_404(City, slug=slug)
    districts = city.districts.all()
    context = {
        'city': city,
        'districts': districts,
        'districts_count': districts.count(),
    }
    return render(request, 'location/city_detail.html', context)


@login_required
def city_create(request):
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.save()
            messages.success(request, f'City "{city.name}" created successfully!')
            return redirect('location:city_detail', slug=city.slug)
    else:
        form = CityForm()
    return render(request, 'location/city_form.html', {'form': form, 'title': 'Add City'})


@login_required
def city_update(request, slug):
    city = get_object_or_404(City, slug=slug)
    if request.method == 'POST':
        form = CityForm(request.POST, instance=city)
        if form.is_valid():
            city = form.save()
            messages.success(request, f'City "{city.name}" updated successfully!')
            return redirect('location:city_detail', slug=city.slug)
    else:
        form = CityForm(instance=city)
    return render(request, 'location/city_form.html', {'form': form, 'title': 'Edit City', 'city': city})


@login_required
def city_delete(request, slug):
    city = get_object_or_404(City, slug=slug)
    if request.method == 'POST':
        city_name = city.name
        city.delete()
        messages.success(request, f'City "{city_name}" deleted successfully!')
        return redirect('location:city_list')
    return render(request, 'location/city_confirm_delete.html', {'city': city})


# District Views
@login_required
def district_list(request):
    districts = District.objects.select_related('city__state__country')
    return render(request, 'location/district_list.html', {'districts': districts})


@login_required
def district_detail(request, slug):
    district = get_object_or_404(District, slug=slug)
    regions = district.regions.all()
    context = {
        'district': district,
        'regions': regions,
        'regions_count': regions.count(),
    }
    return render(request, 'location/district_detail.html', context)


@login_required
def district_create(request):
    if request.method == 'POST':
        form = DistrictForm(request.POST)
        if form.is_valid():
            district = form.save()
            messages.success(request, f'District "{district.name}" created successfully!')
            return redirect('location:district_detail', slug=district.slug)
    else:
        form = DistrictForm()
    return render(request, 'location/district_form.html', {'form': form, 'title': 'Add District'})


@login_required
def district_update(request, slug):
    district = get_object_or_404(District, slug=slug)
    if request.method == 'POST':
        form = DistrictForm(request.POST, instance=district)
        if form.is_valid():
            district = form.save()
            messages.success(request, f'District "{district.name}" updated successfully!')
            return redirect('location:district_detail', slug=district.slug)
    else:
        form = DistrictForm(instance=district)
    return render(request, 'location/district_form.html', {'form': form, 'title': 'Edit District', 'district': district})


@login_required
def district_delete(request, slug):
    district = get_object_or_404(District, slug=slug)
    if request.method == 'POST':
        district_name = district.name
        district.delete()
        messages.success(request, f'District "{district_name}" deleted successfully!')
        return redirect('location:district_list')
    return render(request, 'location:district_confirm_delete.html', {'district': district})


# Region Views
@login_required
def region_list(request):
    regions = Region.objects.select_related('district__city__state__country')
    return render(request, 'location/region_list.html', {'regions': regions})


@login_required
def region_detail(request, slug):
    region = get_object_or_404(Region, slug=slug)
    return render(request, 'location/region_detail.html', {'region': region})


@login_required
def region_create(request):
    if request.method == 'POST':
        form = RegionForm(request.POST)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region "{region.name}" created successfully!')
            return redirect('location:region_detail', slug=region.slug)
    else:
        form = RegionForm()
    return render(request, 'location/region_form.html', {'form': form, 'title': 'Add Region'})


@login_required
def region_update(request, slug):
    region = get_object_or_404(Region, slug=slug)
    if request.method == 'POST':
        form = RegionForm(request.POST, instance=region)
        if form.is_valid():
            region = form.save()
            messages.success(request, f'Region "{region.name}" updated successfully!')
            return redirect('location:region_detail', slug=region.slug)
    else:
        form = RegionForm(instance=region)
    return render(request, 'location/region_form.html', {'form': form, 'title': 'Edit Region', 'region': region})


@login_required
def region_delete(request, slug):
    region = get_object_or_404(Region, slug=slug)
    if request.method == 'POST':
        region_name = region.name
        region.delete()
        messages.success(request, f'Region "{region_name}" deleted successfully!')
        return redirect('location:region_list')
    return render(request, 'location/region_confirm_delete.html', {'region': region})


# AJAX Views for dynamic dropdowns
@login_required
def states_by_country(request, country_id):
    states = State.objects.filter(country_id=country_id).values('id', 'name')
    return JsonResponse(list(states), safe=False)


@login_required
def cities_by_state(request, state_id):
    # Return cities that belong to this state (City has FK to State)
    cities = City.objects.filter(state_id=state_id).values('id', 'name')
    return JsonResponse(list(cities), safe=False)


@login_required
def districts_by_city(request, city_id):
    # Return districts that belong to this city (District has FK to City)
    districts = District.objects.filter(city_id=city_id).values('id', 'name')
    return JsonResponse(list(districts), safe=False)

@login_required
def regions_by_district(request, district_id):
    # Return regions that belong to this district (Region has FK to District)
    regions = Region.objects.filter(district_id=district_id).values('id', 'name')
    return JsonResponse(list(regions), safe=False)
