from django.contrib import admin
from .models import HomePageVideo, ContactMessage
from .models import SoftDeleteAdminMixin


@admin.register(HomePageVideo)
class HomePageVideoAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['activate_selected', 'deactivate_selected']

    def activate_selected(self, request, queryset):
        """Activate selected videos"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Activated {updated} videos.')

    def deactivate_selected(self, request, queryset):
        """Deactivate selected videos"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated} videos.')

    activate_selected.short_description = "Activate selected videos"
    deactivate_selected.short_description = "Deactivate selected videos"


@admin.register(ContactMessage)
class ContactMessageAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'is_read', 'user', 'created_at']
    list_filter = ['is_read', 'created_at', 'user']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['created_at', 'updated_at', 'read_at']
    actions = ['mark_as_read_selected', 'mark_as_unread_selected']

    fieldsets = (
        ('Message Details', {
            'fields': ('name', 'email', 'subject', 'message', 'user')
        }),
        ('Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def mark_as_read_selected(self, request, queryset):
        """Mark selected messages as read"""
        count = 0
        for message in queryset:
            if not message.is_read:
                message.mark_as_read()
                count += 1
        self.message_user(request, f'Marked {count} messages as read.')

    def mark_as_unread_selected(self, request, queryset):
        """Mark selected messages as unread"""
        count = 0
        for message in queryset:
            if message.is_read:
                message.is_read = False
                message.read_at = None
                message.save()
                count += 1
        self.message_user(request, f'Marked {count} messages as unread.')

    mark_as_read_selected.short_description = "Mark selected messages as read"
    mark_as_unread_selected.short_description = "Mark selected messages as unread"