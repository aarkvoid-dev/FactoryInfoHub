from django.urls import path
from . import views



urlpatterns = [
    path('', views.home, name='home'),
    path('contact/', views.contact, name='contact'),
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
