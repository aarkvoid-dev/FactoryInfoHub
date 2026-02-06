"""
Blog application mixins.

This module contains reusable mixins for blog views, providing common functionality
such as location cascading, user authorization, and form handling.
"""

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.utils.translation import gettext as _
from django.shortcuts import get_object_or_404
from django.http import Http404
from .utils import get_location_cascading_queryset, log_user_activity


class LocationCascadingMixin:
    """
    Mixin for handling location cascading in forms.
    
    This mixin provides methods to dynamically update location field querysets
    based on user selections in cascading dropdowns.
    """
    
    def setup_location_fields(self):
        """
        Setup location field querysets based on form data.
        
        This method should be called in form __init__ to update location
        field querysets based on parent selections.
        """
        if self.data:
            # Handle country cascading
            if 'country' in self.data:
                country_id = self.data.get('country')
                self.fields['state'].queryset = get_location_cascading_queryset('state', country_id)
            
            # Handle state cascading
            if 'state' in self.data:
                state_id = self.data.get('state')
                self.fields['city'].queryset = get_location_cascading_queryset('city', state_id)
            
            # Handle city cascading
            if 'city' in self.data:
                city_id = self.data.get('city')
                self.fields['district'].queryset = get_location_cascading_queryset('district', city_id)
            
            # Handle district cascading
            if 'district' in self.data:
                district_id = self.data.get('district')
                self.fields['region'].queryset = get_location_cascading_queryset('region', district_id)
    
    def get_location_initial_values(self):
        """
        Get initial values for location fields based on instance.
        
        Returns:
            dict: Dictionary of initial values for location fields
        """
        initial = {}
        if self.instance and self.instance.region:
            region = self.instance.region
            initial.update({
                'country': region.district.city.state.country,
                'state': region.district.city.state,
                'city': region.district.city,
                'district': region.district,
                'region': region,
            })
        return initial


class UserFormMixin:
    """
    Mixin for common user form functionality.
    
    Provides methods for saving forms with user association and logging activities.
    """
    
    def save_with_user(self, commit=True, author=None):
        """
        Save form instance with user association.
        
        Args:
            commit (bool): Whether to save to database immediately
            author (User): User to associate with the instance
        
        Returns:
            Model instance: The saved instance
        """
        instance = super().save(commit=False)
        if author:
            instance.author = author
        
        if commit:
            instance.save()
        return instance


class BlogAuthorRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only blog authors can access certain views.
    
    This mixin checks if the current user is the author of the blog post
    or if they are a staff member with appropriate permissions.
    """
    
    def test_func(self):
        """Test if user has permission to access the view."""
        blog_post = self.get_object()
        return (
            self.request.user == blog_post.author or 
            self.request.user.is_staff or 
            self.request.user.has_perm('blog.change_blogpost')
        )
    
    def handle_no_permission(self):
        """Handle cases where user doesn't have permission."""
        messages.error(self.request, _('You do not have permission to access this resource.'))
        raise Http404(_("You are not the author of this blog post."))


class BlogAdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin to ensure only admin users can access admin views.
    
    This mixin checks if the current user is a staff member.
    """
    
    def test_func(self):
        """Test if user is staff."""
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        """Handle cases where user doesn't have permission."""
        messages.error(self.request, _('You do not have permission to access this resource.'))
        raise Http404(_("Admin access required."))


class ActivityLoggingMixin:
    """
    Mixin for logging user activities.
    
    Provides methods to log user actions for audit trail purposes.
    """
    
    def log_activity(self, action, details=None):
        """
        Log user activity.
        
        Args:
            action (str): Description of the action
            details (str, optional): Additional details
        """
        log_user_activity(
            user=self.request.user,
            action=action,
            details=details,
            blog_post=getattr(self, 'object', None)
        )
    
    def form_valid(self, form):
        """Override form_valid to add activity logging."""
        response = super().form_valid(form)
        self.log_activity(f"Updated blog post: {self.object.title}")
        return response
    
    def delete(self, request, *args, **kwargs):
        """Override delete to add activity logging."""
        blog_post = self.get_object()
        self.log_activity(f"Deleted blog post: {blog_post.title}")
        return super().delete(request, *args, **kwargs)


class ImageHandlingMixin:
    """
    Mixin for handling image uploads in views.
    
    Provides methods for processing multiple image uploads and managing
    featured images.
    """
    
    def handle_images(self, blog_post):
        """
        Handle image uploads for a blog post.
        
        Args:
            blog_post (BlogPost): The blog post to associate images with
        """
        images = self.request.FILES.getlist('images')
        if images:
            from .utils import handle_multiple_images
            handle_multiple_images(blog_post, images, featured_first=True)
    
    def set_featured_image(self, blog_post, image_id):
        """
        Set a specific image as featured.
        
        Args:
            blog_post (BlogPost): The blog post instance
            image_id (int): ID of the image to set as featured
        
        Returns:
            bool: True if successful, False otherwise
        """
        from .utils import set_featured_image
        return set_featured_image(blog_post, image_id)
    
    def delete_image(self, blog_post, image_id):
        """
        Delete a specific image.
        
        Args:
            blog_post (BlogPost): The blog post instance
            image_id (int): ID of the image to delete
        
        Returns:
            bool: True if successful, False otherwise
        """
        from .utils import delete_blog_image
        return delete_blog_image(image_id, blog_post)


class CategoryCascadingMixin:
    """
    Mixin for handling category cascading in forms.
    
    Provides methods to dynamically update category field querysets
    based on user selections.
    """
    
    def setup_category_fields(self):
        """
        Setup category field querysets based on form data.
        
        This method should be called in form __init__ to update category
        field querysets based on parent selections.
        """
        if self.data:
            # Handle category cascading
            if 'category' in self.data:
                category_id = self.data.get('category')
                if category_id:
                    try:
                        category_id = int(category_id)
                        from category.models import SubCategory
                        self.fields['subcategory'].queryset = SubCategory.objects.filter(
                            category_id=category_id
                        ).order_by('name')
                    except (ValueError, TypeError):
                        pass
    
    def get_category_initial_values(self):
        """
        Get initial values for category fields based on instance.
        
        Returns:
            dict: Dictionary of initial values for category fields
        """
        initial = {}
        if self.instance and self.instance.subcategory:
            initial.update({
                'category': self.instance.subcategory.category,
                'subcategory': self.instance.subcategory,
            })
        return initial