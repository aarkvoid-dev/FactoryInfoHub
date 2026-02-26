from django.contrib import admin
from django.utils.safestring import mark_safe
from django import forms
from .models import Factory, FactoryImage

class FactoryAdminForm(forms.ModelForm):
    class Meta:
        model = Factory
        fields = '__all__'
        widgets = {
            'country': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('country').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'state': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('state').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'city': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('city').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'district': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('district').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'region': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('region').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'category': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('category').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'subcategory': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('subcategory').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
            'created_by': admin.widgets.AutocompleteSelect(
                Factory._meta.get_field('created_by').remote_field,
                admin.site,
                attrs={'data-dropdown-auto-width': 'true'}
            ),
        }

@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    form = FactoryAdminForm
    list_display = ['name', 'city', 'state', 'country', 'created_by', 'is_active', 'is_verified', 'contact_person', 'contact_email', 'image_tag', 'image_count', 'is_deleted']
    list_filter = ['category', 'subcategory', 'city__state__country', 'is_active', 'is_verified', 'is_deleted', 'created_by', 'created_at']
    search_fields = ['name', 'address', 'contact_person', 'contact_email', 'contact_phone', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at', 'slug']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'subcategory')
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
        ('Media', {
            'fields': ('video_url',),
            'classes': ('collapse',)
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
        primary_image = obj.get_primary_image()
        if primary_image:
            return mark_safe(f'<img src="{primary_image}" width="100" height="100" style="border-radius: 8px;" />')
        return "No image"
    image_tag.short_description = 'Primary Image'
    image_tag.allow_tags = True

    def image_count(self, obj):
        return obj.image_count
    image_count.short_description = 'Image Count'

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