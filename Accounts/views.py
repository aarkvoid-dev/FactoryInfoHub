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
from .forms import CustomUserCreationForm, CustomUserChangeForm, CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm,ProfileForm
from .utils import (
    validate_user_registration_data, update_user_profile, send_password_reset_email,
    validate_password_reset_token, get_user_dashboard_data, format_user_display_name,
    send_email_verification, verify_email_token, check_rate_limit, increment_rate_limit,
    log_user_activity, enforce_password_policy
)

def register(request):
    """
    User registration view with email verification.
    
    Handles user registration with validation, email verification,
    and security measures.
    
    Args:
        request (HttpRequest): HTTP request object
    
    Returns:
        HttpResponse: Redirect to verification page or render registration form
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Create profile for the new user
            from .models import Profile
            profile = Profile.objects.create(user=user)
            
            # Send email verification
            if send_email_verification(user, request):
                messages.success(request, _('Registration successful! Please check your email to verify your account.'))
                return redirect('email_verification_sent')
            else:
                messages.error(request, _('Registration successful, but we could not send the verification email. Please contact support.'))
                return redirect('login')
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
    User login view with security features.
    
    Handles user authentication with rate limiting, account lockout,
    and proper error handling.
    
    Args:
        request (HttpRequest): HTTP request object
    
    Returns:
        HttpResponse: Redirect to profile or render login form
    """
    # Check rate limiting
    is_limited, remaining_time = check_rate_limit(request, 'login', max_attempts=5, window_minutes=15)
    if is_limited:
        minutes, seconds = divmod(int(remaining_time), 60)
        messages.error(request, 
            _('Too many login attempts. Please try again in {} minutes and {} seconds.').format(minutes, seconds))
        return render(request, 'accounts/login.html')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if user exists
        try:
            user = User.objects.get(username=username)
            profile = user.profile
            
            # Check if account is locked
            if profile.is_account_locked():
                messages.error(request, _('Your account is temporarily locked due to too many failed login attempts. Please try again later.'))
                increment_rate_limit(request, 'login')
                log_user_activity(user, 'login_attempt_blocked', 'Account locked', request)
                return render(request, 'accounts/login.html')
            
            # Check if email is verified (optional - you can make this required)
            if not profile.email_verified:
                messages.warning(request, _('Please verify your email address to complete your account setup.'))
            
        except User.DoesNotExist:
            # Don't reveal if user exists or not
            pass
        
        # Attempt authentication
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if user is active
            if not user.is_active:
                messages.error(request, _('Your account has been deactivated. Please contact support.'))
                increment_rate_limit(request, 'login')
                log_user_activity(user, 'login_attempt_blocked', 'Account inactive', request)
                return render(request, 'accounts/login.html')
            
            # Successful login
            login(request, user)
            user.profile.reset_failed_attempts()
            log_user_activity(user, 'login_success', None, request)
            messages.success(request, _('Login successful!'))
            
            # Handle "Remember Me" functionality
            if request.POST.get('remember'):
                # Set session expiry to 2 weeks (1209600 seconds)
                request.session.set_expiry(1209600)
            else:
                # Session expires when browser closes
                request.session.set_expiry(0)
            
            # Redirect to profile or next page
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('profile')
        else:
            # Failed login
            try:
                user = User.objects.get(username=username)
                user.profile.increment_failed_attempts()
                log_user_activity(user, 'login_failed', 'Invalid password', request)
            except User.DoesNotExist:
                # Increment rate limit even for non-existent users
                pass
            
            increment_rate_limit(request, 'login')
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
    # Optimize queries by prefetching related data
    user = User.objects.select_related('profile').prefetch_related(
        'profile__factory__category',
        'profile__factory__subcategory',
        'profile__factory__country',
        'profile__factory__state',
        'profile__factory__city'
    ).get(pk=request.user.pk)
    
    if request.method == 'POST':
        user_form = CustomUserChangeForm(request.POST, instance=user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Save user form
            user_form.save()
            
            # Save profile form
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            messages.success(request, _('Profile updated successfully!'))
            return redirect('profile')
        else:
            # Add form validation errors to messages
            for field, errors in user_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            for field, errors in profile_form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        user_form = CustomUserChangeForm(instance=user)
        profile_form = ProfileForm(instance=user.profile)
    
    # Get dashboard data for display
    dashboard_data = get_user_dashboard_data(user)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'dashboard_data': dashboard_data,
        'display_name': format_user_display_name(user),
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
    # Check rate limiting for password reset
    is_limited, remaining_time = check_rate_limit(request, 'password_reset', max_attempts=3, window_minutes=60)
    if is_limited:
        minutes, seconds = divmod(int(remaining_time), 60)
        messages.error(request, 
            _('Too many password reset attempts. Please try again in {} minutes and {} seconds.').format(minutes, seconds))
        return render(request, 'accounts/password_reset.html')
    
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
            
            # Increment rate limit counter
            increment_rate_limit(request, 'password_reset')
            
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


def email_verification_sent(request):
    """Email verification sent confirmation page."""
    return render(request, 'accounts/email_verification_sent.html')


def verify_email(request, uidb64, token):
    """
    Email verification view.
    
    Validates email verification tokens and verifies user email.
    
    Args:
        request (HttpRequest): HTTP request object
        uidb64 (str): Base64 encoded user ID
        token (str): Email verification token
    
    Returns:
        HttpResponse: Render verification result page
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and verify_email_token(user, token):
        messages.success(request, _('Your email has been verified successfully!'))
        return render(request, 'accounts/email_verified.html')
    else:
        messages.error(request, _('The verification link is invalid or has expired.'))
        return render(request, 'accounts/email_verification_invalid.html')
