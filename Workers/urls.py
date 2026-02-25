from django.urls import path
from . import views

app_name = 'workers'

urlpatterns = [
    path('register/', views.register_worker, name='register_worker'),
    path('profile/', views.worker_profile, name='worker_profile'),
    path('profile/edit/<slug:slug>/', views.edit_worker_profile, name='edit_worker_profile'),
    path('add-experience/', views.add_work_experience, name='add_work_experience'),
    path('edit-experience/<int:experience_id>/', views.edit_work_experience, name='edit_work_experience'),
    path('delete-experience/<int:experience_id>/', views.delete_work_experience, name='delete_work_experience'),
    path('detail/<slug:slug>/', views.worker_detail, name='worker_detail'),
    
    # AJAX endpoints for dynamic form updates
   
]
