"""
FAQ application URL configuration.

This module contains the URL patterns for the FAQ application.
"""

from django.urls import path
from . import views

app_name = 'faq'

urlpatterns = [
    # Home and listing views
    path('', views.faq_home, name='home'),
    path('questions/', views.faq_all_questions, name='all_questions'),
    path('question/<slug:slug>/', views.faq_question_detail, name='question_detail'),
    
    # Search functionality
    path('search/', views.faq_search, name='search'),
    
    # Feedback and interaction
    path('question/<slug:slug>/feedback/', views.submit_feedback, name='submit_feedback'),
    
    # Statistics (admin only)
    path('statistics/', views.faq_statistics, name='statistics'),
]