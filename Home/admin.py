from django.contrib import admin
from .models import HomePageVideo, ContactMessage, ContactReply, Page, PageSection
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


@admin.register(ContactReply)
class ContactReplyAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['contact_message', 'admin_user', 'subject', 'email_status', 'sent_at']
    list_filter = ['email_status', 'sent_at', 'admin_user']
    search_fields = ['subject', 'message', 'recipient_email']
    readonly_fields = ['sent_at']


class PageSectionInline(admin.TabularInline):
    model = PageSection
    extra = 0
    fields = ['title', 'content', 'order']
    ordering = ['order']


@admin.register(Page)
class PageAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'page_type', 'order', 'is_published', 'created_at']
    list_filter = ['page_type', 'is_published', 'created_at']
    search_fields = ['title', 'slug', 'content']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [PageSectionInline]
    ordering = ['order', 'title']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type', 'order', 'is_published')
        }),
        ('Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['set_order_to_zero', 'set_order_to_one', 'set_order_to_two', 'set_order_to_three', 'set_order_to_four']

    def set_order_to_zero(self, request, queryset):
        """Set order to 0 (first position)"""
        updated = queryset.update(order=0)
        self.message_user(request, f'Set order to 0 for {updated} pages.')

    def set_order_to_one(self, request, queryset):
        """Set order to 1 (second position)"""
        updated = queryset.update(order=1)
        self.message_user(request, f'Set order to 1 for {updated} pages.')

    def set_order_to_two(self, request, queryset):
        """Set order to 2 (third position)"""
        updated = queryset.update(order=2)
        self.message_user(request, f'Set order to 2 for {updated} pages.')

    def set_order_to_three(self, request, queryset):
        """Set order to 3 (fourth position)"""
        updated = queryset.update(order=3)
        self.message_user(request, f'Set order to 3 for {updated} pages.')

    def set_order_to_four(self, request, queryset):
        """Set order to 4 (fifth position)"""
        updated = queryset.update(order=4)
        self.message_user(request, f'Set order to 4 for {updated} pages.')

    set_order_to_zero.short_description = "Set order to 0 (First)"
    set_order_to_one.short_description = "Set order to 1 (Second)"
    set_order_to_two.short_description = "Set order to 2 (Third)"
    set_order_to_three.short_description = "Set order to 3 (Fourth)"
    set_order_to_four.short_description = "Set order to 4 (Fifth)"


@admin.register(PageSection)
class PageSectionAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['page', 'title', 'order']
    list_filter = ['page', 'order']
    search_fields = ['title', 'content']
