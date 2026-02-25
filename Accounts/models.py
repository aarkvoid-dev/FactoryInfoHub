from django.db import models
from django.contrib.auth.models import User
from Karkahan.models import Factory
from django.utils import timezone
from django.core.validators import FileExtensionValidator

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