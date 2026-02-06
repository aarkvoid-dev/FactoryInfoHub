"""
Blog application utility functions.

This module contains utility functions for common operations across the blog application,
including image handling, location cascading, user activity logging, and form processing.
"""

from django.utils import timezone
from django.contrib import messages
from django.utils.translation import gettext as _
from django.db import transaction
from .models import BlogImage
from location.models import Country, State, City, District, Region
from category.models import Category, SubCategory


def handle_multiple_images(blog_post, images, featured_first=True):
    """
    Handle multiple image uploads for blog posts.
    
    Args:
        blog_post (BlogPost): The blog post instance to associate images with
        images (list): List of uploaded image files
        featured_first (bool): Whether to set the first image as featured
    
    Returns:
        None
    """
    if not images:
        return
    
    for i, image in enumerate(images):
        BlogImage.objects.create(
            blog_post=blog_post,
            image=image,
            order=blog_post.images.count() + i,
            is_featured=(i == 0) if featured_first else False
        )


def get_location_cascading_data():
    """
    Get location data for cascading dropdowns.
    
    Returns:
        dict: Dictionary containing location querysets for forms
    """
    return {
        'countries': Country.objects.all(),
        'states': State.objects.none(),
        'cities': City.objects.none(),
        'districts': District.objects.none(),
        'regions': Region.objects.none(),
    }


def get_location_cascading_queryset(field_name, parent_id):
    """
    Get queryset for location cascading based on parent selection.
    
    Args:
        field_name (str): Name of the location field (country, state, city, district, region)
        parent_id (int): ID of the parent location
    
    Returns:
        QuerySet: Filtered queryset for the specified location field
    """
    if not parent_id:
        return {
            'country': Country.objects.all(),
            'state': State.objects.none(),
            'city': City.objects.none(),
            'district': District.objects.none(),
            'region': Region.objects.none(),
        }.get(field_name, Country.objects.all())
    
    try:
        parent_id = int(parent_id)
        if field_name == 'state':
            return State.objects.filter(country_id=parent_id).order_by('name')
        elif field_name == 'city':
            return City.objects.filter(state_id=parent_id).order_by('name')
        elif field_name == 'district':
            return District.objects.filter(city_id=parent_id).order_by('name')
        elif field_name == 'region':
            return Region.objects.filter(district_id=parent_id).order_by('name')
    except (ValueError, TypeError):
        pass
    
    return {
        'country': Country.objects.all(),
        'state': State.objects.none(),
        'city': City.objects.none(),
        'district': District.objects.none(),
        'region': Region.objects.none(),
    }.get(field_name, Country.objects.all())


def log_user_activity(user, action, details=None, blog_post=None):
    """
    Log user activities for audit trail.
    
    Args:
        user (User): The user performing the action
        action (str): Description of the action performed
        details (str, optional): Additional details about the action
        blog_post (BlogPost, optional): Blog post related to the action
    
    Returns:
        None
    """
    # This is a placeholder for activity logging
    # In a production system, you might want to create an Activity model
    # and log these activities to the database
    pass


def set_featured_image(blog_post, image_id):
    """
    Set a specific image as the featured image for a blog post.
    
    Args:
        blog_post (BlogPost): The blog post instance
        image_id (int): ID of the image to set as featured
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Unset all featured images for this blog post
        blog_post.images.update(is_featured=False)
        
        # Set the specified image as featured
        image = blog_post.images.get(id=image_id)
        image.is_featured = True
        image.save()
        
        return True
    except BlogImage.DoesNotExist:
        return False


def delete_blog_image(image_id, blog_post):
    """
    Delete a specific image from a blog post.
    
    Args:
        image_id (int): ID of the image to delete
        blog_post (BlogPost): The blog post instance
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        image = blog_post.images.get(id=image_id)
        image.delete()
        return True
    except BlogImage.DoesNotExist:
        return False


def get_blog_statistics():
    """
    Get blog statistics for admin dashboard.
    
    Returns:
        dict: Dictionary containing blog statistics
    """
    from .models import BlogPost
    from django.db.models import Count
    
    total_posts = BlogPost.objects.all_with_deleted().count()
    published_posts = BlogPost.objects.filter(is_published=True).count()
    draft_posts = BlogPost.objects.filter(is_published=False, is_deleted=False).count()
    deleted_posts = BlogPost.objects.deleted_only().count()
    
    # Category distribution
    category_stats = BlogPost.objects.values('subcategory__name').annotate(
        count=Count('id')
    ).order_by('-count')[:5]
    
    return {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'deleted_posts': deleted_posts,
        'category_stats': category_stats,
    }


def validate_blog_data(data):
    """
    Validate blog post data before saving.
    
    Args:
        data (dict): Dictionary containing blog post data
    
    Returns:
        tuple: (is_valid, errors) where is_valid is boolean and errors is dict
    """
    errors = {}
    
    # Validate required fields
    required_fields = ['title', 'content']
    for field in required_fields:
        if not data.get(field):
            errors[field] = _('This field is required.')
    
    # Validate title length
    title = data.get('title', '')
    if len(title) < 5:
        errors['title'] = _('Title must be at least 5 characters long.')
    
    # Validate content length
    content = data.get('content', '')
    if len(content) < 20:
        errors['content'] = _('Content must be at least 20 characters long.')
    
    return len(errors) == 0, errors


def create_blog_notification(user, blog_post, action):
    """
    Create a notification for blog post actions.
    
    Args:
        user (User): User who performed the action
        blog_post (BlogPost): Blog post related to the notification
        action (str): Type of action (created, updated, published, etc.)
    
    Returns:
        None
    """
    # This is a placeholder for notification system
    # In a production system, you might want to create a Notification model
    # and send email notifications to subscribers
    pass