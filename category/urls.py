from django.urls import path
from . import views

app_name = 'category'

urlpatterns = [
    # Dashboard
    path('', views.category_dashboard, name='dashboard'),

    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_create, name='category_create'),
    path('categories/<slug:slug>/', views.category_detail, name='category_detail'),
    path('categories/<slug:slug>/edit/', views.category_update, name='category_update'),
    path('categories/<slug:slug>/delete/', views.category_delete, name='category_delete'),

    # SubCategory URLs
    path('subcategories/', views.subcategory_list, name='subcategory_list'),
    path('subcategories/add/', views.subcategory_create, name='subcategory_create'),
    path('subcategories/<slug:slug>/', views.subcategory_detail, name='subcategory_detail'),
    path('subcategories/<slug:slug>/edit/', views.subcategory_update, name='subcategory_update'),
    path('subcategories/<slug:slug>/delete/', views.subcategory_delete, name='subcategory_delete'),

    # AJAX URLs for dynamic dropdowns
    path('ajax/load-subcategories/<int:category_id>/', views.ajax_load_subcategories, name='ajax_load_subcategories'),
]
