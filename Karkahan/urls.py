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
    path('factories/<slug:slug>/restore/', views.factory_restore, name='factory_restore'),
    path('factories/<slug:slug>/hard-delete/', views.factory_hard_delete, name='factory_hard_delete'),
    
    # Factory status management
    path('factories/<slug:slug>/toggle-active/', views.factory_toggle_active, name='factory_toggle_active'),
    path('factories/<slug:slug>/toggle-verified/', views.factory_toggle_verified, name='factory_toggle_verified'),
    
    
    # AJAX endpoints for dynamic form updates
    path('ajax/get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('ajax/get-states/', views.get_states, name='get_states'),
    path('ajax/get-cities/', views.get_cities, name='get_cities'),
    path('ajax/get-districts/', views.get_districts, name='get_districts'),
    path('ajax/get-regions/', views.get_regions, name='get_regions'),
    
    
    # Email Testing
    path('test-email/', views.test_email, name='test_email'),

    # Cart
    path('cart/add/<slug:factory_slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/add-api/<slug:factory_slug>/', views.add_to_cart_api, name='add_to_cart_api'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/', views.cart_detail, name='cart_detail'),

    # Checkout
    path('checkout/initiate/', views.initiate_checkout, name='initiate_checkout'),
    path('checkout/success/', views.checkout_success, name='checkout_success'),

    # Webhook
    path('webhook/stripe/', views.stripe_webhook, name='stripe_webhook'),
    path('webhook/razorpay/', views.razorpay_webhook, name='razorpay_webhook'),

    # Order history
    path('orders/', views.order_history, name='order_history'),
    
    # Payment error handling
    path('payment/failed/', views.payment_failed, name='payment_failed'),
    path('payment/retry/<int:order_id>/', views.retry_payment, name='retry_payment'),
    
    # Email management
    path('order/<int:order_id>/resend-email/', views.resend_order_email, name='resend_order_email'),
    
    # New user-facing order resolution URLs
    path('order/<int:order_id>/reinitiate/', views.reinitiate_payment, name='reinitiate_payment'),
    path('order/<int:order_id>/verify/', views.verify_payment_status, name='verify_payment_status'),
    path('order/<int:order_id>/report-issue/', views.report_payment_issue, name='report_payment_issue'),
]
