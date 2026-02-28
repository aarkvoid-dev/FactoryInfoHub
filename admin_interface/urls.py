from django.urls import path
from . import views

app_name = 'admin_interface'

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('api/', views.admin_dashboard_api, name='admin_dashboard_api'),
    path('users/', views.admin_users, name='admin_users'),
    path('users/create/', views.admin_user_create, name='admin_user_create'),
    path('users/edit/<int:user_id>/', views.admin_user_edit, name='admin_user_edit'),
    path('users/delete/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    path('factories/', views.admin_factories, name='admin_factories'),
    path('workers/', views.admin_workers, name='admin_workers'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('notifications/', views.admin_notifications, name='admin_notifications'),
    path('profile/', views.admin_profile, name='admin_profile'),
    
    # Location Management
    path('locations/', views.admin_locations, name='admin_locations'),
    path('locations/countries/', views.admin_countries, name='admin_countries'),
    path('locations/states/', views.admin_states, name='admin_states'),
    path('locations/cities/', views.admin_cities, name='admin_cities'),
    path('locations/districts/', views.admin_districts, name='admin_districts'),
    path('locations/regions/', views.admin_regions, name='admin_regions'),
    
    # Category Management
    path('categories/', views.admin_categories, name='admin_categories'),
    path('categories/subcategories/', views.admin_subcategories, name='admin_subcategories'),
    
    # CRUD URLs for Factories
    path('factories/create/', views.admin_factory_create, name='admin_factory_create'),
    path('factories/edit/<int:factory_id>/', views.admin_factory_edit, name='admin_factory_edit'),
    path('factories/delete/<int:factory_id>/', views.admin_factory_delete, name='admin_factory_delete'),
    path('factories/restore/<int:factory_id>/', views.admin_factory_restore, name='admin_factory_restore'),
    path('factories/detail/<int:factory_id>/', views.admin_factory_detail, name='admin_factory_detail'),
    
    # CRUD URLs for Workers
    path('workers/create/', views.admin_worker_create, name='admin_worker_create'),
    path('workers/edit/<int:worker_id>/', views.admin_worker_edit, name='admin_worker_edit'),
    path('workers/delete/<int:worker_id>/', views.admin_worker_delete, name='admin_worker_delete'),
    path('workers/restore/<int:worker_id>/', views.admin_worker_restore, name='admin_worker_restore'),
    path('workers/detail/<int:worker_id>/', views.admin_worker_detail, name='admin_worker_detail'),
    
    # CRUD URLs for Blogs
    path('blogs/', views.admin_blogs, name='admin_blogs'),
    path('blogs/create/', views.admin_blog_create, name='admin_blog_create'),
    path('blogs/edit/<int:blog_id>/', views.admin_blog_edit, name='admin_blog_edit'),
    path('blogs/delete/<int:blog_id>/', views.admin_blog_delete, name='admin_blog_delete'),
    path('blogs/restore/<int:blog_id>/', views.admin_blog_restore, name='admin_blog_restore'),
    path('blogs/detail/<int:blog_id>/', views.admin_blog_detail, name='admin_blog_detail'),
    path('blogs/images/<int:blog_id>/', views.admin_blog_images, name='admin_blog_images'),
    
    # CRUD URLs for FAQ
    path('faq/', views.admin_faq, name='admin_faq'),
    path('faq/create/', views.admin_faq_create, name='admin_faq_create'),
    path('faq/edit/<int:question_id>/', views.admin_faq_edit, name='admin_faq_edit'),
    path('faq/delete/<int:question_id>/', views.admin_faq_delete, name='admin_faq_delete'),
    path('faq/restore/<int:question_id>/', views.admin_faq_restore, name='admin_faq_restore'),
    path('faq/detail/<int:question_id>/', views.admin_faq_detail, name='admin_faq_detail'),
    
    # Contact Messages URLs
    path('contacts/', views.admin_contacts, name='admin_contacts'),
    path('contacts/mark-read/<int:message_id>/', views.mark_message_read, name='mark_message_read'),
    path('contacts/delete/<int:message_id>/', views.delete_message, name='delete_message'),
    path('contacts/bulk-actions/', views.bulk_actions, name='bulk_actions'),
    
    # Home Page Videos URLs
    path('videos/', views.admin_homepage_videos, name='admin_homepage_videos'),
    path('videos/create/', views.admin_homepage_video_create, name='admin_homepage_video_create'),
    path('videos/edit/<int:video_id>/', views.admin_homepage_video_edit, name='admin_homepage_video_edit'),
    path('videos/delete/<int:video_id>/', views.admin_homepage_video_delete, name='admin_homepage_video_delete'),
    path('videos/restore/<int:video_id>/', views.admin_homepage_video_restore, name='admin_homepage_video_restore'),
    path('videos/permanent-delete/<int:video_id>/', views.admin_homepage_video_permanent_delete, name='admin_homepage_video_permanent_delete'),
    path('videos/detail/<int:video_id>/', views.admin_homepage_video_detail, name='admin_homepage_video_detail'),
]