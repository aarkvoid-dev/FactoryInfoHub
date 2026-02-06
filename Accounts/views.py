"""
Accounts application views module.

This module contains all the view functions for user authentication, registration,
profile management, and password handling.

Functions:
    register: User registration view
    login_view: User login view
    logout_view: User logout view
    profile: User profile management view
    change_password: Password change view
    password_reset_request: Password reset request view
    password_reset_done: Password reset done confirmation view
    password_reset_confirm: Password reset confirmation view
    password_reset_complete: Password reset completion view
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.core.mail import BadHeaderError
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.translation import gettext as _
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm
from .utils import (
    validate_user_registration_data, update_user_profile, send_password_reset_email,
    validate_password_reset_token, get_user_dashboard_data, format_user_display_name
)

def register(request):
    """
    User registration view.
    
    Handles user registration with validation and error handling.
    
    Args:
        request (HttpRequest): HTTP request object
    
    Returns:
        HttpResponse: Redirect to profile or render registration form
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, _('Registration successful!'))
            return redirect('profile')
        else:
            # Add form validation errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    """
    User login view.
    
    Handles user authentication with proper error handling and security logging.
    
    Args:
        request (HttpRequest): HTTP request object
    
    Returns:
        HttpResponse: Redirect to profile or render login form
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Log login attempt
        # log_user_login_attempt(username, success=False)  # Will be implemented
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # log_user_login_attempt(username, success=True)  # Will be implemented
            messages.success(request, _('Login successful!'))
            return redirect('profile')
        else:
            # log_user_login_attempt(username, success=False)  # Will be implemented
            messages.error(request, _('Invalid username or password.'))
    
    return render(request, 'accounts/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('login')

@login_required
def profile(request):
    """
    User profile management view.
    
    Handles user profile viewing and editing with proper validation.
    
    Args:
        request (HttpRequest): HTTP request object
    
    Returns:
        HttpResponse: Render profile form or redirect after successful update
    """
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            # Use utility function for profile updates
            success, errors = update_user_profile(request.user, form.cleaned_data)
            if success:
                messages.success(request, _('Profile updated successfully!'))
                return redirect('profile')
            else:
                # Add validation errors to form
                for field, error in errors.items():
                    form.add_error(field, error)
        else:
            # Add form validation errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserChangeForm(instance=request.user)
    
    # Get dashboard data for display
    dashboard_data = get_user_dashboard_data(request.user)
    
    context = {
        'form': form,
        'dashboard_data': dashboard_data,
        'display_name': format_user_display_name(request.user),
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password changed successfully!')
            return redirect('profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'accounts/change_password.html', {'form': form})

def password_reset_request(request):
    """
    Password reset request view.
    
    Handles password reset requests with proper email validation and security measures.
    
    Args:
        request (HttpRequest): HTTP request object
    
    Returns:
        HttpResponse: Redirect to done page or render password reset form
    """
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Always show success message regardless of email existence for security
            associated_users = User.objects.filter(email=email, is_active=True)
            if associated_users.exists():
                for user in associated_users:
                    # Use utility function to send password reset email
                    if not send_password_reset_email(user, request):
                        messages.error(request, _('An error occurred while sending the email. Please try again later.'))
                        return render(request, 'accounts/password_reset.html', {'form': form})
            
            # Always show success message to prevent email enumeration
            messages.success(request, _('If an account with that email exists, a password reset link has been sent.'))
            return redirect("password_reset_done")
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})

def password_reset_done(request):
    return render(request, 'accounts/password_reset_done.html')

def password_reset_confirm(request, uidb64, token):
    """
    Password reset confirmation view.
    
    Validates password reset tokens and handles password reset confirmation.
    
    Args:
        request (HttpRequest): HTTP request object
        uidb64 (str): Base64 encoded user ID
        token (str): Password reset token
    
    Returns:
        HttpResponse: Render password reset form or redirect to login
    """
    # Use utility function to validate token
    user = validate_password_reset_token(uidb64, token)
    
    if user is not None:
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _('Password has been reset successfully!'))
                return redirect('login')
        else:
            form = CustomSetPasswordForm(user)
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, _('The reset password link is no longer valid.'))
        return redirect('login')

def password_reset_complete(request):
    return render(request, 'accounts/password_reset_complete.html')
