"""
Accounts application utility functions.

This module contains utility functions for common operations across the accounts application,
including user management, authentication helpers, and form processing.
"""

from django.contrib import messages
from django.utils.translation import gettext as _
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError
from django.utils import timezone


def validate_username_uniqueness(username):
    """
    Validate that username is unique.
    
    Args:
        username (str): Username to validate
    
    Returns:
        bool: True if username is unique, False otherwise
    """
    return not User.objects.filter(username=username).exists()


def validate_email_uniqueness(email):
    """
    Validate that email is unique.
    
    Args:
        email (str): Email to validate
    
    Returns:
        bool: True if email is unique, False otherwise
    """
    return not User.objects.filter(email=email).exists()


def validate_password_match(password1, password2):
    """
    Validate that two passwords match.
    
    Args:
        password1 (str): First password
        password2 (str): Second password
    
    Returns:
        bool: True if passwords match, False otherwise
    """
    return password1 == password2


def validate_password_strength(password):
    """
    Validate password strength requirements.
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, _('Password must be at least 8 characters long.')
    
    if password.isdigit():
        return False, _('Password cannot be entirely numeric.')
    
    # Check for at least one letter
    if not any(c.isalpha() for c in password):
        return False, _('Password must contain at least one letter.')
    
    return True, None


def send_password_reset_email(user, request):
    """
    Send password reset email to user.
    
    Args:
        user (User): User to send email to
        request (HttpRequest): Current request object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        import ssl
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        subject = _("Password Reset Requested")
        email_template_name = "accounts/password_reset_email.txt"
        c = {
            "email": user.email,
            'domain': request.META['HTTP_HOST'],
            'site_name': 'FactoryInfoHub',
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "user": user,
            'token': default_token_generator.make_token(user),
            'protocol': 'https' if request.is_secure() else 'http',
        }
        email_body = render_to_string(email_template_name, c)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = user.email
        
        # Add HTML content
        html_part = MIMEText(email_body, 'html')
        msg.attach(html_part)
        
        # Send email with SSL context that bypasses certificate verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls(context=context)
            if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception:
        return False


def log_user_login_attempt(username, success=True):
    """
    Log user login attempts for security monitoring.
    
    Args:
        username (str): Username attempted
        success (bool): Whether login was successful
    
    Returns:
        None
    """
    # This is a placeholder for login attempt logging
    # In a production system, you might want to create a LoginAttempt model
    # and log these attempts to the database for security monitoring
    pass


def get_user_profile_data(user):
    """
    Get user profile data for display.
    
    Args:
        user (User): User instance
    
    Returns:
        dict: Dictionary containing user profile information
    """
    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name(),
        'date_joined': user.date_joined,
        'last_login': user.last_login,
        'is_active': user.is_active,
        'is_staff': user.is_staff,
    }


def update_user_profile(user, data):
    """
    Update user profile with validated data.
    
    Args:
        user (User): User instance to update
        data (dict): Dictionary containing updated profile data
    
    Returns:
        tuple: (success, errors) where success is bool and errors is dict
    """
    errors = {}
    
    # Validate email uniqueness if changed
    email = data.get('email')
    if email and email != user.email:
        if not validate_email_uniqueness(email):
            errors['email'] = _('A user with that email address already exists.')
    
    # Validate username uniqueness if changed
    username = data.get('username')
    if username and username != user.username:
        if not validate_username_uniqueness(username):
            errors['username'] = _('A user with that username already exists.')
    
    if errors:
        return False, errors
    
    # Update user fields
    if 'username' in data:
        user.username = data['username']
    if 'email' in data:
        user.email = data['email']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    user.save()
    return True, {}


def validate_user_registration_data(data):
    """
    Validate user registration data.
    
    Args:
        data (dict): Dictionary containing registration data
    
    Returns:
        tuple: (is_valid, errors) where is_valid is bool and errors is dict
    """
    errors = {}
    
    # Validate required fields
    required_fields = ['username', 'email', 'password1', 'password2']
    for field in required_fields:
        if not data.get(field):
            errors[field] = _('This field is required.')
    
    # Validate username
    username = data.get('username', '')
    if username and not validate_username_uniqueness(username):
        errors['username'] = _('A user with that username already exists.')
    
    # Validate email
    email = data.get('email', '')
    if email and not validate_email_uniqueness(email):
        errors['email'] = _('A user with that email address already exists.')
    
    # Validate passwords
    password1 = data.get('password1', '')
    password2 = data.get('password2', '')
    
    if password1 and password2:
        if not validate_password_match(password1, password2):
            errors['password2'] = _("The two password fields didn't match.")
        
        is_valid, error_msg = validate_password_strength(password1)
        if not is_valid:
            errors['password1'] = error_msg
    
    return len(errors) == 0, errors


def create_user_activity_log(user, action, details=None):
    """
    Create user activity log entry.
    
    Args:
        user (User): User who performed the action
        action (str): Description of the action
        details (str, optional): Additional details
    
    Returns:
        None
    """
    # This is a placeholder for activity logging
    # In a production system, you might want to create an Activity model
    # and log these activities to the database
    pass


def get_user_dashboard_data(user):
    """
    Get user dashboard data.
    
    Args:
        user (User): User instance
    
    Returns:
        dict: Dictionary containing dashboard data
    """
    # This is a placeholder for dashboard data
    # In a real application, you might want to include:
    # - Recent blog posts by user
    # - User statistics
    # - Notifications
    # - Activity summary
    
    return {
        'user': user,
        'profile_data': get_user_profile_data(user),
        'recent_activity': [],  # Placeholder for recent activity
        'statistics': {},  # Placeholder for user statistics
    }


def format_user_display_name(user):
    """
    Format user display name for templates.
    
    Args:
        user (User): User instance
    
    Returns:
        str: Formatted display name
    """
    full_name = user.get_full_name()
    if full_name:
        return full_name
    return user.username


def validate_password_reset_token(uidb64, token):
    """
    Validate password reset token.
    
    Args:
        uidb64 (str): Base64 encoded user ID
        token (str): Password reset token
    
    Returns:
        User or None: User instance if valid, None otherwise
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None

    if user is not None and default_token_generator.check_token(user, token):
        return user
    
    return None


def generate_email_verification_token():
    """
    Generate a secure email verification token.
    
    Returns:
        str: Generated token
    """
    import secrets
    return secrets.token_urlsafe(32)


def send_email_verification(user, request):
    """
    Send email verification to user.
    
    Args:
        user (User): User instance
        request (HttpRequest): Current request object
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        from .models import Profile
        profile = user.profile
        
        # Generate verification token
        token = generate_email_verification_token()
        profile.email_verification_token = token
        profile.email_verification_sent_at = timezone.now()
        profile.save()
        
        # Send verification email with SSL certificate verification disabled
        import ssl
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        subject = _("Please verify your email address")
        email_template_name = "accounts/email_verification_email.txt"
        c = {
            "user": user,
            "email": user.email,
            'domain': request.META['HTTP_HOST'],
            'site_name': 'FactoryInfoHub',
            "uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "token": token,
            'protocol': 'https' if request.is_secure() else 'http',
        }
        email_body = render_to_string(email_template_name, c)
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.DEFAULT_FROM_EMAIL
        msg['To'] = user.email
        
        # Add HTML content
        html_part = MIMEText(email_body, 'html')
        msg.attach(html_part)
        
        # Send email with SSL context that bypasses certificate verification
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            if settings.EMAIL_USE_TLS:
                server.starttls(context=context)
            if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD:
                server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print("Error is :",e)
        return False


def verify_email_token(user, token):
    """
    Verify email verification token.
    
    Args:
        user (User): User instance
        token (str): Email verification token
    
    Returns:
        bool: True if token is valid, False otherwise
    """
    from .models import Profile
    try:
        profile = user.profile
        if profile.email_verification_token == token:
            # Check if token is not expired (valid for 24 hours)
            if profile.email_verification_sent_at:
                from django.utils import timezone
                from datetime import timedelta
                if timezone.now() - profile.email_verification_sent_at < timedelta(hours=24):
                    profile.email_verified = True
                    profile.email_verification_token = None
                    profile.email_verification_sent_at = None
                    profile.save()
                    return True
    except Profile.DoesNotExist:
        pass
    return False


def check_rate_limit(request, action='login', max_attempts=5, window_minutes=15):
    """
    Check if user has exceeded rate limit for an action.
    
    Args:
        request (HttpRequest): Current request object
        action (str): Type of action to rate limit
        max_attempts (int): Maximum attempts allowed
        window_minutes (int): Time window in minutes
    
    Returns:
        tuple: (is_limited, remaining_time)
    """
    from django.core.cache import cache
    import time
    
    # Create cache key based on IP and action
    ip = get_client_ip(request)
    cache_key = f"rate_limit_{action}_{ip}"
    
    # Get current attempts and window start time
    data = cache.get(cache_key, {'attempts': 0, 'window_start': time.time()})
    
    current_time = time.time()
    window_start = data['window_start']
    attempts = data['attempts']
    
    # Check if window has expired
    if current_time - window_start > window_minutes * 60:
        # Reset window
        data = {'attempts': 0, 'window_start': current_time}
        attempts = 0
    
    # Check if rate limit exceeded
    if attempts >= max_attempts:
        remaining_time = window_minutes * 60 - (current_time - window_start)
        return True, max(0, remaining_time)
    
    return False, 0


def increment_rate_limit(request, action='login', window_minutes=15):
    """
    Increment rate limit counter for an action.
    
    Args:
        request (HttpRequest): Current request object
        action (str): Type of action to rate limit
        window_minutes (int): Time window in minutes
    """
    from django.core.cache import cache
    import time
    
    ip = get_client_ip(request)
    cache_key = f"rate_limit_{action}_{ip}"
    
    # Get current data or initialize
    data = cache.get(cache_key, {'attempts': 0, 'window_start': time.time()})
    current_time = time.time()
    
    # Check if window has expired
    if current_time - data['window_start'] > window_minutes * 60:
        # Reset window
        data = {'attempts': 1, 'window_start': current_time}
    else:
        # Increment attempts
        data['attempts'] += 1
    
    # Set cache with expiration
    cache.set(cache_key, data, window_minutes * 60)


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request (HttpRequest): Current request object
    
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_user_activity(user, action, details=None, request=None):
    """
    Log user activity for security monitoring.
    
    Args:
        user (User): User who performed the action
        action (str): Description of the action
        details (str, optional): Additional details
        request (HttpRequest, optional): Current request object
    
    Returns:
        None
    """
    # This is a placeholder for activity logging
    # In a production system, you might want to create an Activity model
    # and log these activities to the database
    import logging
    logger = logging.getLogger('accounts.activity')
    
    ip_address = get_client_ip(request) if request else 'unknown'
    log_data = {
        'user_id': user.id if user else None,
        'username': user.username if user else 'anonymous',
        'action': action,
        'details': details,
        'ip_address': ip_address,
        'timestamp': timezone.now().isoformat()
    }
    
    logger.info(f"User activity: {log_data}")


def validate_password_history(user, new_password):
    """
    Validate that new password is not in user's password history.
    
    Args:
        user (User): User instance
        new_password (str): New password to validate
    
    Returns:
        bool: True if password is not in history, False otherwise
    """
    # This is a placeholder - in production you'd want to store
    # password hashes in a PasswordHistory model
    return True


def enforce_password_policy(password):
    """
    Enforce comprehensive password policy.
    
    Args:
        password (str): Password to validate
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, _('Password must be at least 8 characters long.')
    
    if len(password) > 128:
        return False, _('Password must be less than 128 characters long.')
    
    if password.isdigit():
        return False, _('Password cannot be entirely numeric.')
    
    # Check for at least one letter
    if not any(c.isalpha() for c in password):
        return False, _('Password must contain at least one letter.')
    
    # Check for common passwords (basic check)
    common_passwords = ['password', '12345678', 'qwerty123', 'admin123']
    if password.lower() in common_passwords:
        return False, _('This password is too common. Please choose a more unique password.')
    
    return True, None
