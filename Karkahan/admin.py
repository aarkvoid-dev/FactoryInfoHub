from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Factory, FactoryImage

@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'country', 'created_by', 'is_active', 'is_verified', 'contact_person', 'contact_email', 'image_tag', 'is_deleted']
    list_filter = ['category', 'subcategory', 'city__state__country', 'is_active', 'is_verified', 'is_deleted', 'created_by', 'created_at']
    search_fields = ['name', 'address', 'contact_person', 'contact_email', 'contact_phone', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'slug']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'subcategory')
        }),
        ('Factory Image', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Location Details', {
            'fields': ('country', 'state', 'city', 'district', 'region', 'address', 'pincode')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email', 'website')
        }),
        ('Factory Specifications', {
            'fields': ('factory_type', 'production_capacity', 'working_hours', 'holidays')
        }),
        ('Business Details', {
            'fields': ('established_year', 'employee_count', 'annual_turnover')
        }),
        ('Creator Information', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    autocomplete_fields = ['city', 'state', 'country', 'district', 'region', 'category', 'subcategory', 'created_by']

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" height="100" style="border-radius: 8px;" />')
        return "No image"
    image_tag.short_description = 'Image Preview'
    image_tag.allow_tags = True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('city', 'state', 'country', 'district', 'region', 'category', 'subcategory')

    def full_address(self, obj):
        return obj.full_address
    full_address.short_description = "Full Address"
    full_address.admin_order_field = 'address'

@admin.register(FactoryImage)
class FactoryImageAdmin(admin.ModelAdmin):
    list_display = ['factory', 'image_tag', 'alt_text', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['factory__name', 'alt_text']
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['factory']

    def image_tag(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="60" height="60" style="border-radius: 4px;" />')
        return "No image"
    image_tag.short_description = 'Image Preview'
    image_tag.allow_tags = True