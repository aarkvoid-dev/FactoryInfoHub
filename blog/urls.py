from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.BlogPostListView.as_view(), name='post_list'),
    path('create/', views.create_blog_post_form, name='post_create'),
    path('create-manual/', views.create_blog_post, name='post_create_manual'),
    path('admin/', views.blog_admin_dashboard, name='admin_dashboard'),
    path('upload-image/', views.tinymce_image_upload, name='upload_image'),
    path('<slug:slug>/', views.BlogPostDetailView.as_view(), name='post_detail'),
    path('<slug:slug>/update/', views.BlogPostUpdateView.as_view(), name='post_update'),
    path('<slug:slug>/delete/', views.BlogPostDeleteView.as_view(), name='post_delete'),
    path('<slug:slug>/manage-images/', views.manage_images, name='manage_images'),
    
    # Blog Delete Operations
    path('<slug:slug>/soft-delete/', views.blog_soft_delete, name='blog_soft_delete'),
    path('<slug:slug>/hard-delete/', views.blog_hard_delete, name='blog_hard_delete'),
    path('<slug:slug>/restore/', views.blog_restore, name='blog_restore'),
]
