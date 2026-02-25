from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from .models import Profile

class ProfileInline(admin.StackedInline):
    """Inline admin for Profile model to be displayed in User admin."""
    model = Profile
    can_delete = False
    verbose_name = 'Profile'
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = (
        'factory', 'role', 'profile_image', 'date_of_birth', 'gender', 
        'phone_number', 'address', 'email_notifications', 'in_app_notifications',
        'email_verified', 'failed_login_attempts', 'locked_until', 'last_password_change'
    )
    readonly_fields = ('failed_login_attempts', 'locked_until', 'last_password_change', 'profile_image_preview')
    
    def profile_image_preview(self, obj):
        """Display profile image preview in admin."""
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="100" height="100" style="border-radius: 50%;" />')
        return "No image"
    profile_image_preview.short_description = "Profile Image Preview"


class UserAdmin(BaseUserAdmin):
    """Custom UserAdmin that includes Profile information."""
    inlines = (ProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 
        'is_active', 'get_factory', 'get_role', 'get_email_verified', 'last_login'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'groups', 
        'profile__factory', 'profile__role', 'profile__email_verified'
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__factory__name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    def get_factory(self, obj):
        """Get factory name for display in list."""
        return obj.profile.factory.name if obj.profile.factory else 'No Factory'
    get_factory.short_description = 'Factory'
    get_factory.admin_order_field = 'profile__factory__name'
    
    def get_role(self, obj):
        """Get user role for display in list."""
        return obj.profile.role if obj.profile else 'No Profile'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'
    
    def get_email_verified(self, obj):
        """Get email verification status for display in list."""
        return obj.profile.email_verified if obj.profile else False
    get_email_verified.short_description = 'Email Verified'
    get_email_verified.boolean = True
    get_email_verified.admin_order_field = 'profile__email_verified'


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Standalone Profile admin for direct access."""
    list_display = [
        'user', 'factory', 'role', 'email_verified', 'failed_login_attempts', 
        'is_account_locked', 'last_password_change', 'created_at'
    ]
    list_filter = [
        'factory', 'role', 'email_verified', 'email_notifications', 
        'in_app_notifications', 'created_at'
    ]
    search_fields = ['user__username', 'user__email', 'factory__name', 'phone_number']
    readonly_fields = [
        'user', 'failed_login_attempts', 'locked_until', 'last_password_change', 
        'created_at', 'updated_at', 'profile_image_preview'
    ]
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'factory', 'role')
        }),
        ('Personal Information', {
            'fields': ('profile_image', 'profile_image_preview', 'date_of_birth', 'gender', 'phone_number', 'address')
        }),
        ('Email Verification', {
            'fields': ('email_verified', 'email_verification_token', 'email_verification_sent_at')
        }),
        ('Security', {
            'fields': ('failed_login_attempts', 'locked_until', 'last_password_change')
        }),
        ('Notifications', {
            'fields': ('email_notifications', 'in_app_notifications')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def profile_image_preview(self, obj):
        """Display profile image preview in admin."""
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="100" height="100" style="border-radius: 50%;" />')
        return "No image"
    profile_image_preview.short_description = "Profile Image Preview"
    
    def is_account_locked(self, obj):
        """Check if account is locked."""
        return obj.is_account_locked()
    is_account_locked.boolean = True
    is_account_locked.short_description = "Locked?"
    
    def unlock_user_account(self, request, queryset):
        """Custom admin action to unlock user accounts."""
        for profile in queryset:
            profile.unlock_account()
        self.message_user(request, f"Successfully unlocked {queryset.count()} account(s).")
    unlock_user_account.short_description = "Unlock selected accounts"
    
    actions = [unlock_user_account]
