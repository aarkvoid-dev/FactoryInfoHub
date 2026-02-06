from django.contrib import admin
from Home.models import SoftDeleteAdminMixin
from .models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(SoftDeleteAdminMixin, admin.ModelAdmin):
    list_display = ['title', 'author', 'subcategory', 'region', 'is_published', 'is_deleted', 'published_at', 'created_at']
    list_filter = ['is_published', 'is_deleted', 'subcategory', 'region', 'published_at', 'created_at']
    search_fields = ['title', 'content', 'author__username']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    ordering = ['-created_at']
    actions = SoftDeleteAdminMixin.actions + ['publish_selected', 'unpublish_selected']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Categorization', {
            'fields': ('category', 'subcategory', 'country', 'state', 'city', 'district', 'region')
        }),
        ('Publishing', {
            'fields': ('author', 'is_published', 'published_at')
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def publish_selected(self, request, queryset):
        """Publish selected blog posts"""
        count = 0
        for post in queryset:
            if not post.is_published:
                post.is_published = True
                from django.utils import timezone
                if not post.published_at:
                    post.published_at = timezone.now()
                post.save()
                count += 1
        self.message_user(request, f'Successfully published {count} blog posts.')

    def unpublish_selected(self, request, queryset):
        """Unpublish selected blog posts"""
        count = queryset.filter(is_published=True).update(is_published=False, published_at=None)
        self.message_user(request, f'Successfully unpublished {count} blog posts.')

    publish_selected.short_description = "Publish selected posts"
    unpublish_selected.short_description = "Unpublish selected posts"
