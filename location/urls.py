from django.urls import path
from . import views

app_name = 'location'

urlpatterns = [
    # Dashboard
    path('', views.location_dashboard, name='dashboard'),

    # Country URLs
    path('countries/', views.country_list, name='country_list'),
    path('countries/add/', views.country_create, name='country_create'),
    path('countries/<slug:slug>/', views.country_detail, name='country_detail'),
    path('countries/<slug:slug>/edit/', views.country_update, name='country_update'),
    path('countries/<slug:slug>/delete/', views.country_delete, name='country_delete'),

    # State URLs
    path('states/', views.state_list, name='state_list'),
    path('states/add/', views.state_create, name='state_create'),
    path('states/<slug:slug>/', views.state_detail, name='state_detail'),
    path('states/<slug:slug>/edit/', views.state_update, name='state_update'),
    path('states/<slug:slug>/delete/', views.state_delete, name='state_delete'),

    # District URLs
    path('districts/', views.district_list, name='district_list'),
    path('districts/add/', views.district_create, name='district_create'),
    path('districts/<slug:slug>/', views.district_detail, name='district_detail'),
    path('districts/<slug:slug>/edit/', views.district_update, name='district_update'),
    path('districts/<slug:slug>/delete/', views.district_delete, name='district_delete'),

    # City URLs
    path('cities/', views.city_list, name='city_list'),
    path('cities/add/', views.city_create, name='city_create'),
    path('cities/<slug:slug>/', views.city_detail, name='city_detail'),
    path('cities/<slug:slug>/edit/', views.city_update, name='city_update'),
    path('cities/<slug:slug>/delete/', views.city_delete, name='city_delete'),

    # Region URLs
    path('regions/', views.region_list, name='region_list'),
    path('regions/add/', views.region_create, name='region_create'),
    path('regions/<slug:slug>/', views.region_detail, name='region_detail'),
    path('regions/<slug:slug>/edit/', views.region_update, name='region_update'),
    path('regions/<slug:slug>/delete/', views.region_delete, name='region_delete'),

    # AJAX URLs for dynamic dropdowns
    path('ajax/states-by-country/<int:country_id>/', views.states_by_country, name='states_by_country'),
    path('ajax/cities-by-state/<int:state_id>/', views.cities_by_state, name='cities_by_state'),
    path('ajax/districts-by-city/<int:city_id>/', views.districts_by_city, name='districts_by_city'),
    path('ajax/regions-by-district/<int:district_id>/', views.regions_by_district, name='regions_by_district'),
]
