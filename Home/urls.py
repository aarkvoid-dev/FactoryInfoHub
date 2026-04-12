from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('contact/enquiry/', views.contact, {'type': 'enquiry'}, name='contact_enquiry'),
    path('contact/export/', views.contact, {'type': 'export'}, name='contact_export'),
    path('contact/karigar/', views.contact, {'type': 'karigar'}, name='contact_karigar'),
    path('contact/online-class/', views.contact, {'type': 'online_class'}, name='contact_online_class'),
    # Keep legacy contact URL as redirect to enquiry (optional)
    path('contact/', views.contact, {'type': 'enquiry'}, name='contact'),
    path('products/', views.products, name='products'),
    
    # Dynamic page system
    path('page/<slug:slug>/', views.page_detail, name='page_detail'),
    
    # Legacy URLs that redirect to dynamic pages
    path('terms-and-conditions/', views.terms_and_conditions_view, name='terms_and_conditions'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('about-us/', views.about_us_view, name='about_us'),
    path('disclaimer/', views.disclaimer_view, name='disclaimer'),
    path('refund-policy/', views.refund_policy_view, name='refund_policy'),
]
