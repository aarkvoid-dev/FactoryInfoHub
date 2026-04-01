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
    path('users/reset-password/<int:user_id>/', views.admin_user_reset_password, name='admin_user_reset_password'),
    path('factories/', views.admin_factories, name='admin_factories'),
    path('workers/', views.admin_workers, name='admin_workers'),
    path('reports/', views.admin_reports, name='admin_reports'),
    path('notifications/', views.admin_notifications, name='admin_notifications'),
    path('profile/', views.admin_profile, name='admin_profile'),
    
    # Location Management
    path('locations/', views.admin_locations, name='admin_locations'),
    
    # Countries CRUD
    path('locations/countries/', views.admin_countries, name='admin_countries'),
    path('locations/countries/create/', views.admin_country_create, name='admin_country_create'),
    path('locations/countries/edit/<int:country_id>/', views.admin_country_edit, name='admin_country_edit'),
    path('locations/countries/delete/<int:country_id>/', views.admin_country_delete, name='admin_country_delete'),
    path('locations/countries/restore/<int:country_id>/', views.admin_country_restore, name='admin_country_restore'),
    path('locations/countries/detail/<int:country_id>/', views.admin_country_detail, name='admin_country_detail'),
    
    # States CRUD
    path('locations/states/', views.admin_states, name='admin_states'),
    path('locations/states/create/', views.admin_state_create, name='admin_state_create'),
    path('locations/states/edit/<int:state_id>/', views.admin_state_edit, name='admin_state_edit'),
    path('locations/states/delete/<int:state_id>/', views.admin_state_delete, name='admin_state_delete'),
    path('locations/states/restore/<int:state_id>/', views.admin_state_restore, name='admin_state_restore'),
    path('locations/states/detail/<int:state_id>/', views.admin_state_detail, name='admin_state_detail'),
    
    # Cities CRUD
    path('locations/cities/', views.admin_cities, name='admin_cities'),
    path('locations/cities/create/', views.admin_city_create, name='admin_city_create'),
    path('locations/cities/edit/<int:city_id>/', views.admin_city_edit, name='admin_city_edit'),
    path('locations/cities/delete/<int:city_id>/', views.admin_city_delete, name='admin_city_delete'),
    path('locations/cities/restore/<int:city_id>/', views.admin_city_restore, name='admin_city_restore'),
    path('locations/cities/detail/<int:city_id>/', views.admin_city_detail, name='admin_city_detail'),
    
    # Districts CRUD
    path('locations/districts/', views.admin_districts, name='admin_districts'),
    path('locations/districts/create/', views.admin_district_create, name='admin_district_create'),
    path('locations/districts/edit/<int:district_id>/', views.admin_district_edit, name='admin_district_edit'),
    path('locations/districts/delete/<int:district_id>/', views.admin_district_delete, name='admin_district_delete'),
    path('locations/districts/restore/<int:district_id>/', views.admin_district_restore, name='admin_district_restore'),
    path('locations/districts/detail/<int:district_id>/', views.admin_district_detail, name='admin_district_detail'),
    
    # Regions CRUD
    path('locations/regions/', views.admin_regions, name='admin_regions'),
    path('locations/regions/create/', views.admin_region_create, name='admin_region_create'),
    path('locations/regions/edit/<int:region_id>/', views.admin_region_edit, name='admin_region_edit'),
    path('locations/regions/delete/<int:region_id>/', views.admin_region_delete, name='admin_region_delete'),
    path('locations/regions/restore/<int:region_id>/', views.admin_region_restore, name='admin_region_restore'),
    path('locations/regions/detail/<int:region_id>/', views.admin_region_detail, name='admin_region_detail'),
    
    # Category Management
    path('categories/', views.admin_categories, name='admin_categories'),
    path('categories/create/', views.admin_category_create, name='admin_category_create'),
    path('categories/edit/<int:category_id>/', views.admin_category_edit, name='admin_category_edit'),
    path('categories/delete/<int:category_id>/', views.admin_category_delete, name='admin_category_delete'),
    path('categories/restore/<int:category_id>/', views.admin_category_restore, name='admin_category_restore'),
    path('categories/detail/<int:category_id>/', views.admin_category_detail, name='admin_category_detail'),
    
    path('categories/subcategories/', views.admin_subcategories, name='admin_subcategories'),
    path('categories/subcategories/create/', views.admin_subcategory_create, name='admin_subcategory_create'),
    path('categories/subcategories/edit/<int:subcategory_id>/', views.admin_subcategory_edit, name='admin_subcategory_edit'),
    path('categories/subcategories/delete/<int:subcategory_id>/', views.admin_subcategory_delete, name='admin_subcategory_delete'),
    path('categories/subcategories/restore/<int:subcategory_id>/', views.admin_subcategory_restore, name='admin_subcategory_restore'),
    path('categories/subcategories/detail/<int:subcategory_id>/', views.admin_subcategory_detail, name='admin_subcategory_detail'),
    
    # CRUD URLs for Factories
    path('factories/create/', views.admin_factory_create, name='admin_factory_create'),
    path('factories/edit/<int:factory_id>/', views.admin_factory_edit, name='admin_factory_edit'),
    path('factories/delete/<int:factory_id>/', views.admin_factory_delete, name='admin_factory_delete'),
    path('factories/restore/<int:factory_id>/', views.admin_factory_restore, name='admin_factory_restore'),
    path('factories/hard-delete/<int:factory_id>/', views.admin_factory_hard_delete, name='admin_factory_hard_delete'),
    path('factories/detail/<int:factory_id>/', views.admin_factory_detail, name='admin_factory_detail'),
    
    # CRUD URLs for Workers
    path('workers/create/', views.admin_worker_create, name='admin_worker_create'),
    path('workers/edit/<int:worker_id>/', views.admin_worker_edit, name='admin_worker_edit'),
    path('workers/delete/<int:worker_id>/', views.admin_worker_delete, name='admin_worker_delete'),
    path('workers/restore/<int:worker_id>/', views.admin_worker_restore, name='admin_worker_restore'),
    path('workers/hard-delete/<int:worker_id>/', views.admin_worker_hard_delete, name='admin_worker_hard_delete'),
    path('workers/detail/<int:worker_id>/', views.admin_worker_detail, name='admin_worker_detail'),
    
    # CRUD URLs for Blogs
    path('blogs/', views.admin_blogs, name='admin_blogs'),
    path('blogs/create/', views.admin_blog_create, name='admin_blog_create'),
    path('blogs/edit/<int:blog_id>/', views.admin_blog_edit, name='admin_blog_edit'),
    path('blogs/delete/<int:blog_id>/', views.admin_blog_delete, name='admin_blog_delete'),
    path('blogs/restore/<int:blog_id>/', views.admin_blog_restore, name='admin_blog_restore'),
    path('blogs/detail/<int:blog_id>/', views.admin_blog_detail, name='admin_blog_detail'),
    path('blogs/images/<int:blog_id>/', views.admin_blog_images, name='admin_blog_images'),
    
    # Blog Delete Operations
    path('blogs/soft-delete/<int:blog_id>/', views.admin_blog_soft_delete, name='admin_blog_soft_delete'),
    path('blogs/hard-delete/<int:blog_id>/', views.admin_blog_hard_delete, name='admin_blog_hard_delete'),
    path('blogs/permanent-delete/<int:blog_id>/', views.admin_blog_permanent_delete, name='admin_blog_permanent_delete'),
    
    # CRUD URLs for FAQ
    path('faq/', views.admin_faq_list, name='admin_faq'),
    path('faq/create/', views.admin_faq_create, name='admin_faq_create'),
    path('faq/<int:pk>/edit/', views.admin_faq_edit, name='admin_faq_edit'),
    path('faq/<int:pk>/delete/', views.admin_faq_delete, name='admin_faq_delete'),
    
    # Contact Messages URLs
    path('contacts/', views.admin_contacts, name='admin_contacts'),
    path('contacts/detail/<int:message_id>/', views.admin_contact_detail, name='admin_contact_detail'),
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
    
    # Payment Management URLs
    path('payments/', views.admin_payments, name='admin_payments'),
    path('payments/<int:order_id>/', views.admin_payment_detail, name='admin_payment_detail'),
    
    # Payment Gateway URLs
    path('payments/gateways/', views.admin_payment_gateways, name='admin_payment_gateways'),
    path('payments/gateways/create/', views.admin_payment_gateway_create, name='admin_payment_gateway_create'),
    path('payments/gateways/edit/<int:gateway_id>/', views.admin_payment_gateway_edit, name='admin_payment_gateway_edit'),
    path('payments/gateways/delete/<int:gateway_id>/', views.admin_payment_gateway_delete, name='admin_payment_gateway_delete'),
    
    # Order URLs
    path('payments/orders/', views.admin_orders, name='admin_orders'),
    path('payments/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('payments/orders/<int:order_id>/complete/', views.admin_order_complete, name='admin_order_complete'),
    path('payments/orders/<int:order_id>/complete-with-email/', views.admin_complete_order_with_email, name='admin_complete_order_with_email'),
    path('payments/orders/<int:order_id>/retry-email/', views.admin_retry_order_email, name='admin_retry_order_email'),
    path('payments/pending-orders/', views.admin_pending_orders, name='admin_pending_orders'),
    path('payments/orders/delete/<int:order_id>/', views.admin_order_delete, name='admin_order_delete'),
    
    # Order Item URLs
    path('payments/order-items/', views.admin_order_items, name='admin_order_items'),
    path('payments/order-items/<int:item_id>/', views.admin_order_item_detail, name='admin_order_item_detail'),
    path('payments/order-items/delete/<int:item_id>/', views.admin_order_item_delete, name='admin_order_item_delete'),
    
    # Contact Messages API
    path('contacts/mark-messages/', views.mark_messages_api, name='mark_messages_api'),
    
    # Contact Reply System
    path('contacts/reply/<int:message_id>/', views.admin_reply_to_contact, name='admin_reply_to_contact'),
    path('contacts/send-reply/', views.send_contact_reply, name='send_contact_reply'),
    path('contacts/reply-history/<int:message_id>/', views.admin_reply_history, name='admin_reply_history'),

    path('factory-stats/', views.factory_stats, name='factory_stats'),
    path('factory-stats/<int:factory_id>/trackers/', views.factory_tracker_detail, name='factory_tracker_detail'),
    path('factory-stats/charts/', views.factory_stats_charts, name='factory_stats_charts'),
    
    # Page Management URLs
    path('pages/', views.admin_pages, name='admin_pages'),
    path('pages/create/', views.admin_page_create, name='admin_page_create'),
    path('pages/<int:page_id>/edit/', views.admin_page_edit, name='admin_page_edit'),
    path('pages/<int:page_id>/delete/', views.admin_page_delete, name='admin_page_delete'),
    path('pages/<int:page_id>/restore/', views.admin_page_restore, name='admin_page_restore'),
    path('pages/<int:page_id>/permanent-delete/', views.admin_page_permanent_delete, name='admin_page_permanent_delete'),
    path('pages/<int:page_id>/', views.admin_page_detail, name='admin_page_detail'),
    path('pages/<int:page_id>/sections/', views.admin_page_sections, name='admin_page_sections'),
    path('pages/sections/<int:section_id>/edit/', views.admin_page_section_edit, name='admin_page_section_edit'),
    path('pages/sections/<int:section_id>/delete/', views.admin_page_section_delete, name='admin_page_section_delete'),
]
