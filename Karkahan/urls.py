from django.urls import path
from . import views

app_name = 'karkahan'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Factory CRUD operations
    path('factories/', views.factory_list, name='factory_list'),
    path('factories/create/', views.factory_create, name='factory_create'),
    path('factories/<slug:slug>/', views.factory_detail, name='factory_detail'),
    path('factories/<slug:slug>/edit/', views.factory_edit, name='factory_edit'),
    path('factories/<slug:slug>/delete/', views.factory_delete, name='factory_delete'),
    
    # Factory status management
    path('factories/<slug:slug>/toggle-active/', views.factory_toggle_active, name='factory_toggle_active'),
    path('factories/<slug:slug>/toggle-verified/', views.factory_toggle_verified, name='factory_toggle_verified'),
    
    # AJAX endpoints for dynamic form updates
    path('ajax/get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('ajax/get-states/', views.get_states, name='get_states'),
    path('ajax/get-cities/', views.get_cities, name='get_cities'),
    path('ajax/get-districts/', views.get_districts, name='get_districts'),
    path('ajax/get-regions/', views.get_regions, name='get_regions'),
]