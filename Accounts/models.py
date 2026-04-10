from django.db import models
from django.contrib.auth.models import User
from Karkahan.models import Factory
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import hashlib

class Profile(models.Model):
    """
    Custom user profile model for factory information hub.

    This model connects users to their factories and includes comprehensive profile information.
    """

    # Role choices
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('user', 'User'),
    ]

    brand_name = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Your pBrandname"
    )

    # Factory relationship
    factory = models.ForeignKey(
        Factory,
        on_delete=models.CASCADE,
        related_name='profiles',
        help_text="The factory this user is associated with",
        blank=True,
        null=True,
    )

    # Profile image
    profile_image = models.ImageField(
        upload_to='profile_images/',
        blank=True,
        null=True,
        help_text="Profile image for the user",
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )

    # Personal information
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Your date of birth"
    )
    gender = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        help_text="Your gender"
    )
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="Your phone number"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Your address"
    )

    # Role and permissions
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        help_text="User role and permission level"
    )

    # Notification preferences
    email_notifications = models.BooleanField(
        default=True,
        help_text="Receive email notifications"
    )
    in_app_notifications = models.BooleanField(
        default=True,
        help_text="Receive in-app notifications"
    )

    # Email verification
    email_verified = models.BooleanField(default=False, help_text="Whether the user's email is verified")
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    email_verification_sent_at = models.DateTimeField(blank=True, null=True)

    # Account security
    failed_login_attempts = models.PositiveIntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    last_password_change = models.DateTimeField(default=timezone.now)

    # Audit fields
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    # User relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Profile for {self.user.username} - {self.factory.name if self.factory else 'No Factory'}"

    class Meta:
        verbose_name = "Factory Profile"
        verbose_name_plural = "Factory Profiles"
        ordering = ['-created_at']

    def is_account_locked(self):
        """Check if account is locked due to failed login attempts."""
        if self.locked_until and self.locked_until > timezone.now():
            return True
        return False

    def lock_account(self, minutes=30):
        """Lock account for specified minutes."""
        self.locked_until = timezone.now() + timezone.timedelta(minutes=minutes)
        self.save()

    def unlock_account(self):
        """Unlock account."""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save()

    def increment_failed_attempts(self):
        """Increment failed login attempts."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.lock_account()
        self.save()

    def reset_failed_attempts(self):
        """Reset failed login attempts."""
        if self.failed_login_attempts > 0:
            self.failed_login_attempts = 0
            self.save() 


class PasswordHistory(models.Model):
    """
    Model to track user password history for security purposes.
    
    This model stores hashed versions of previous passwords to prevent
    users from reusing old passwords.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_history',
        help_text="User who changed password"
    )
    
    password_hash = models.CharField(
        max_length=128,
        help_text="Hashed version of the password"
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this password was set"
    )
    
    class Meta:
        verbose_name = "Password History"
        verbose_name_plural = "Password History"
        ordering = ['-created_at']
        # Prevent duplicate password hashes for the same user
        unique_together = ['user', 'password_hash']
    
    def __str__(self):
        return f"Password history for {self.user.username} - {self.created_at}"
    
    @classmethod
    def add_password_to_history(cls, user, password):
        """
        Add a password to the user's password history.
        
        Args:
            user (User): User instance
            password (str): Password to hash and store
        """
        # Hash the password using Django's built-in hasher
        password_hash = user.password
        
        # Store only the last 5 passwords to prevent history from growing too large
        existing_count = cls.objects.filter(user=user).count()
        if existing_count >= 5:
            # Remove oldest password if we already have 5
            oldest = cls.objects.filter(user=user).order_by('created_at').first()
            if oldest:
                oldest.delete()
        
        # Create new password history entry
        cls.objects.create(
            user=user,
            password_hash=password_hash
        )
    
    @classmethod
    def check_password_reuse(cls, user, password):
        """
        Check if a password has been used recently by the user.
        
        Args:
            user (User): User instance
            password (str): Password to check
        
        Returns:
            bool: True if password was used recently, False otherwise
        """
        # Get recent password hashes (last 5)
        recent_passwords = cls.objects.filter(user=user).order_by('-created_at')[:5]
        
        # Check if the new password matches any recent password
        for history_entry in recent_passwords:
            if user.check_password(password, history_entry.password_hash):
                return True
        
        return False


class RateLimit(models.Model):
    """
    Model to track rate limiting attempts for various actions.
    
    This model provides persistent rate limiting that survives server restarts.
    """
    
    # Action types
    ACTION_CHOICES = [
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
        ('email_resend', 'Email Resend'),
        ('registration', 'Registration'),
    ]
    
    ip_address = models.GenericIPAddressField(
        help_text="IP address being rate limited"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Type of action being rate limited"
    )
    
    attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of attempts in current window"
    )
    
    window_start = models.DateTimeField(
        help_text="Start time of current rate limiting window"
    )
    
    blocked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the block expires (if currently blocked)"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this rate limit entry was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this rate limit entry was last updated"
    )
    
    class Meta:
        verbose_name = "Rate Limit"
        verbose_name_plural = "Rate Limits"
        unique_together = ['ip_address', 'action']
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Rate limit for {self.ip_address} - {self.action}"
    
    def is_limited(self, max_attempts=5, window_minutes=15):
        """
        Check if this rate limit entry is currently limited.
        
        Args:
            max_attempts (int): Maximum allowed attempts
            window_minutes (int): Window duration in minutes
        
        Returns:
            bool: True if limited, False otherwise
        """
        current_time = timezone.now()
        
        # Check if currently blocked
        if self.blocked_until and self.blocked_until > current_time:
            return True
        
        # Check if window has expired
        window_end = self.window_start + timezone.timedelta(minutes=window_minutes)
        if current_time > window_end:
            # Reset window
            self.attempts = 0
            self.window_start = current_time
            self.save()
            return False
        
        # Check if attempts exceeded
        return self.attempts >= max_attempts
    
    def increment(self):
        """
        Increment the attempt counter for this rate limit entry.
        """
        current_time = timezone.now()
        
        # Check if window has expired
        window_end = self.window_start + timezone.timedelta(minutes=15)  # Default 15 minutes
        if current_time > window_end:
            # Reset window
            self.attempts = 1
            self.window_start = current_time
        else:
            # Increment attempts
            self.attempts += 1
        
        # Check if we should block
        if self.attempts >= 5:  # Default max attempts
            self.blocked_until = current_time + timezone.timedelta(minutes=15)
        
        self.save()
    
    @classmethod
    def get_or_create_rate_limit(cls, ip_address, action):
        """
        Get or create a rate limit entry for the given IP and action.
        
        Args:
            ip_address (str): IP address to rate limit
            action (str): Action type
        
        Returns:
            RateLimit: Rate limit entry
        """
        rate_limit, created = cls.objects.get_or_create(
            ip_address=ip_address,
            action=action,
            defaults={
                'attempts': 0,
                'window_start': timezone.now()
            }
        )
        
        # If not created, check if we need to reset the window
        if not created:
            current_time = timezone.now()
            window_end = rate_limit.window_start + timezone.timedelta(minutes=15)
            if current_time > window_end:
                rate_limit.attempts = 0
                rate_limit.window_start = current_time
                rate_limit.blocked_until = None
                rate_limit.save()
        
        return rate_limit


class UserActivityLog(models.Model):
    """
    Model to track user activities for security monitoring.
    
    This model provides persistent logging of user activities.
    """
    
    ACTION_CHOICES = [
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('login_blocked', 'Login Blocked'),
        ('password_change', 'Password Change'),
        ('password_reset_request', 'Password Reset Request'),
        ('password_reset_complete', 'Password Reset Complete'),
        ('email_verification_sent', 'Email Verification Sent'),
        ('email_verification_failed', 'Email Verification Failed'),
        ('profile_update', 'Profile Update'),
        ('registration', 'Registration'),
        ('logout', 'Logout'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    
    username = models.CharField(
        max_length=150,
        help_text="Username (even if user is deleted)"
    )
    
    action = models.CharField(
        max_length=50,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    
    details = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about the action"
    )
    
    ip_address = models.GenericIPAddressField(
        help_text="IP address from which the action was performed"
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this activity was logged"
    )
    
    class Meta:
        verbose_name = "User Activity Log"
        verbose_name_plural = "User Activity Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} by {self.username} at {self.created_at}"
    
    @classmethod
    def log_activity(cls, user, action, details=None, request=None):
        """
        Log a user activity.
        
        Args:
            user (User): User who performed the action
            action (str): Type of action
            details (str, optional): Additional details
            request (HttpRequest, optional): Current request object
        """
        username = user.username if user else 'anonymous'
        ip_address = 'unknown'
        user_agent = 'unknown'
        
        if request:
            from .utils import get_client_ip
            ip_address = get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        
        cls.objects.create(
            user=user,
            username=username,
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )