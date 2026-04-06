"""
Custom decorators for email verification and user restrictions.

This module provides decorators to enforce email verification requirements
for different types of user actions in the FactoryInfoHub application.
"""

from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _


def email_verified_required(view_func):
    """
    Decorator that requires the user's email to be verified.
    
    This decorator checks if the user's email is verified and blocks access
    to certain functionality if not verified. It provides clear error messages
    and redirects users to appropriate pages.
    
    Usage:
        @email_verified_required
        def my_view(request):
            # View logic here
    
    Args:
        view_func (function): The view function to decorate
        
    Returns:
        function: The decorated view function
        
    Behavior:
        - If user is not logged in: Redirects to login page
        - If user's email is verified: Proceeds with the view
        - If user's email is not verified: Shows error message and redirects to dashboard
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is authenticated (login_required functionality)
        if not request.user.is_authenticated:
            messages.error(request, _('You must be logged in to access this page.'))
            return redirect(f"{reverse('login')}?next={request.path}")
        
        # Check if user's email is verified
        # The email_verified field is in the Profile model, linked to User
        try:
            profile = request.user.profile
            if not profile.email_verified:
                messages.error(
                    request, 
                    _('Your email address is not verified. Please verify your email to access this feature. '
                      'Check your email for a verification link, or go to your profile to resend the verification email.')
                )
                # Redirect to dashboard or profile page where they can verify email
                return redirect('karkahan:factory_list')
        except Exception:
            # If profile doesn't exist, redirect to dashboard
            messages.error(request, _('Please complete your profile setup.'))
            return redirect('karkahan:factory_list')
        
        # If email is verified, proceed with the original view
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def allow_unverified(view_func):
    """
    Decorator that explicitly allows unverified users to access a view.
    
    This decorator is used for views that should be accessible even to users
    who haven't verified their email yet. It's primarily used for worker
    registration and profile management.
    
    Usage:
        @allow_unverified
        def worker_registration_view(request):
            # View logic here
    
    Args:
        view_func (function): The view function to decorate
        
    Returns:
        function: The decorated view function
        
    Note:
        This decorator doesn't add any restrictions - it's mainly for documentation
        purposes to explicitly mark views that should allow unverified users.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # This decorator doesn't add any restrictions
        # It's used to explicitly mark views that allow unverified users
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def require_verified_or_admin(view_func):
    """
    Decorator that requires email verification or admin status.
    
    This decorator allows access if either:
    1. The user's email is verified, OR
    2. The user is an admin/staff member
    
    This is useful for administrative functions that should be accessible
    to staff even if their email isn't verified.
    
    Usage:
        @require_verified_or_admin
        def admin_view(request):
            # View logic here
    
    Args:
        view_func (function): The view function to decorate
        
    Returns:
        function: The decorated view function
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check if user is authenticated
        if not request.user.is_authenticated:
            messages.error(request, _('You must be logged in to access this page.'))
            return redirect(f"{reverse('login')}?next={request.path}")
        
        # Allow access if user is admin/staff
        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Check if user's email is verified
        try:
            profile = request.user.profile
            if not profile.email_verified:
                messages.error(
                    request, 
                    _('Your email address is not verified. Please verify your email to access this feature. '
                      'Check your email for a verification link, or go to your profile to resend the verification email.')
                )
                return redirect('karkahan:dashboard')
        except Exception:
            messages.error(request, _('Please complete your profile setup.'))
            return redirect('karkahan:dashboard')
        
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def profile_complete_required(f=None, redirect_url=None, required_fields=None):
    """
    Decorator to check if user profile is complete before accessing a view.
    If profile is incomplete, redirects to profile page with a message.
    
    This decorator can be combined with email_verified_required.
    
    Args:
        f: The view function (for direct decoration)
        redirect_url (str, optional): URL to redirect to. Defaults to 'accounts:profile'
        required_fields (list, optional): List of required field names. 
                                         Defaults to ['phone_number', 'address']
    
    Usage:
        @profile_complete_required
        def my_view(request):
            pass
        
        @email_verified_required
        @profile_complete_required
        def my_view(request):
            # Both checks will be performed
            pass
        
        @profile_complete_required(redirect_url='accounts:edit_profile')
        def my_view(request):
            pass
        
        @profile_complete_required(required_fields=['phone_number', 'address', 'date_of_birth'])
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Only check for authenticated users
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)
            
            # Get or check profile
            if not hasattr(request.user, 'profile'):
                # No profile exists, redirect to create one
                messages.warning(
                    request, 
                    'Please complete your profile before proceeding.'
                )
                return redirect(redirect_url or 'accounts:profile')
            
            profile = request.user.profile
            
            # Default required fields
            if required_fields is None:
                fields_to_check = ['phone_number', 'address']
            else:
                fields_to_check = required_fields
            
            # Check if any required field is missing
            missing_fields = []
            for field_name in fields_to_check:
                field_value = getattr(profile, field_name, None)
                print("field_value :",field_value)
                if not field_value:
                    # Get verbose field name
                    field_verbose = field_name.replace('_', ' ').title()
                    missing_fields.append(field_verbose)
            
            if missing_fields:
                # Store missing fields in session for the profile page
                request.session['profile_redirect_message'] = (
                    f'Please complete your profile. Missing: {", ".join(missing_fields)}'
                )
                
                messages.warning(
                    request,
                    f'Please complete your profile before proceeding. Missing: {", ".join(missing_fields)}'
                )
                
                return redirect(redirect_url or 'profile')
            
            # Profile is complete, proceed with the view
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    
    # Handle both @profile_complete_required and @profile_complete_required()
    if f:
        return decorator(f)
    return decorator


def check_profile_completion(user):
    """
    Utility function to check if a user's profile is complete.
    
    Args:
        user: Django User instance
    
    Returns:
        tuple: (is_complete: bool, missing_fields: list)
    """
    if not user.is_authenticated:
        return True, []
    
    if not hasattr(user, 'profile'):
        return False, ['profile']
    
    profile = user.profile
    required_fields = ['phone_number', 'address']
    
    missing_fields = []
    for field_name in required_fields:
        field_value = getattr(profile, field_name, None)
        if not field_value:
            field_verbose = field_name.replace('_', ' ').title()
            missing_fields.append(field_verbose)
    
    return len(missing_fields) == 0, missing_fields
