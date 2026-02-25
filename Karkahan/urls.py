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
    
    # Shopping Cart
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<slug:factory_slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:cart_item_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout and Purchase
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/process/', views.process_purchase, name='process_purchase'),
    path('payment/<int:purchase_amount>/', views.payment_page, name='payment_page'),
    path('payment/process/', views.process_payment, name='process_payment'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/failure/', views.payment_failure, name='payment_failure'),
    
    # Purchase History
    path('purchases/', views.purchase_history, name='purchase_history'),
    path('purchases/resend/<int:purchase_id>/', views.resend_purchase_email, name='resend_purchase_email'),
    
    # AJAX endpoints for dynamic form updates
    path('ajax/get-subcategories/', views.get_subcategories, name='get_subcategories'),
    path('ajax/get-states/', views.get_states, name='get_states'),
    path('ajax/get-cities/', views.get_cities, name='get_cities'),
    path('ajax/get-districts/', views.get_districts, name='get_districts'),
    path('ajax/get-regions/', views.get_regions, name='get_regions'),
    
    # Email Testing
    path('test-email/', views.test_email, name='test_email'),
]
