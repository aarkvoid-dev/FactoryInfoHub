from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name = 'Profile'
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    fields = (
        'factory', 'role', 'profile_image', 'date_of_birth', 'gender', 
        'phone_number', 'address', 'email_notifications', 'in_app_notifications',
        'email_verified', 'is_spam', 'failed_login_attempts', 
        'locked_until', 'last_password_change'
    )
    readonly_fields = ('failed_login_attempts', 'locked_until', 'last_password_change', 'profile_image_preview')
    
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="100" height="100" style="border-radius: 50%;" />')
        return "No image"
    profile_image_preview.short_description = "Profile Image Preview"


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = (
        'username', 'email', 'first_name', 'last_name', 'is_staff', 
        'is_active', 'get_factory', 'get_role', 'get_email_verified', 
        'get_is_spam', 'last_login'
    )
    list_filter = (
        'is_staff', 'is_superuser', 'is_active', 'groups', 
        'profile__factory', 'profile__role', 'profile__email_verified',
        'profile__is_spam'   # <-- new filter
    )
    search_fields = ('username', 'first_name', 'last_name', 'email', 'profile__factory__name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets  # keep original
    
    def get_factory(self, obj):
        return obj.profile.factory.name if obj.profile.factory else 'No Factory'
    get_factory.short_description = 'Factory'
    get_factory.admin_order_field = 'profile__factory__name'
    
    def get_role(self, obj):
        return obj.profile.role if obj.profile else 'No Profile'
    get_role.short_description = 'Role'
    get_role.admin_order_field = 'profile__role'
    
    def get_email_verified(self, obj):
        return obj.profile.email_verified if obj.profile else False
    get_email_verified.short_description = 'Email Verified'
    get_email_verified.boolean = True
    get_email_verified.admin_order_field = 'profile__email_verified'
    
    def get_is_spam(self, obj):
        return obj.profile.is_spam if obj.profile else False
    get_is_spam.short_description = 'Spam'
    get_is_spam.boolean = True
    get_is_spam.admin_order_field = 'profile__is_spam'
    
    # Custom actions for spam handling
    actions = ['mark_as_spam', 'unmark_as_spam']
    
    def mark_as_spam(self, request, queryset):
        count = 0
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.is_spam = True
                user.profile.save()
                count += 1
        self.message_user(request, f'Marked {count} user(s) as spam.')
    mark_as_spam.short_description = 'Mark selected users as spam'
    
    def unmark_as_spam(self, request, queryset):
        count = 0
        for user in queryset:
            if hasattr(user, 'profile'):
                user.profile.is_spam = False
                user.profile.save()
                count += 1
        self.message_user(request, f'Unmarked {count} user(s) as spam.')
    unmark_as_spam.short_description = 'Remove spam flag from selected users'


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'factory', 'role', 'email_verified', 'is_spam',
        'failed_login_attempts', 'is_account_locked', 'last_password_change', 'created_at'
    ]
    list_filter = [
        'factory', 'role', 'email_verified', 'is_spam', 'email_notifications', 
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
        ('Spam Detection', {
            'fields': ('is_spam',),
            'classes': ('wide',),
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
        if obj.profile_image:
            return mark_safe(f'<img src="{obj.profile_image.url}" width="100" height="100" style="border-radius: 50%;" />')
        return "No image"
    profile_image_preview.short_description = "Profile Image Preview"
    
    def is_account_locked(self, obj):
        return obj.is_account_locked()
    is_account_locked.boolean = True
    is_account_locked.short_description = "Locked?"
    
    actions = ['unlock_user_account', 'mark_as_spam', 'unmark_as_spam', 'auto_flag_spam']
    
    def unlock_user_account(self, request, queryset):
        for profile in queryset:
            profile.unlock_account()
        self.message_user(request, f'Unlocked {queryset.count()} account(s).')
    unlock_user_account.short_description = "Unlock selected accounts"
    
    def mark_as_spam(self, request, queryset):
        count = queryset.update(is_spam=True)
        self.message_user(request, f'Marked {count} profile(s) as spam.')
    mark_as_spam.short_description = "Mark as spam"
    
    def unmark_as_spam(self, request, queryset):
        count = queryset.update(is_spam=False)
        self.message_user(request, f'Unmarked {count} profile(s) as spam.')
    unmark_as_spam.short_description = "Remove spam flag"
    
    def auto_flag_spam(self, request, queryset):
        """
        Run the spam_suspected() manager method and flag those profiles.
        Optionally, you can run it on all profiles, not just selected.
        """
        # Apply to all profiles – ignore the queryset selection for simplicity
        suspected = Profile.objects.spam_suspected()
        count = suspected.update(is_spam=True)
        self.message_user(request, f'Auto-flagged {count} suspected spam profiles.')
    auto_flag_spam.short_description = "Auto-flag suspected spam (based on heuristics)"