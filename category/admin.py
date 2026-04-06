from django.contrib import admin
from django.utils.html import format_html
from .models import Category, SubCategory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_image', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['slug', 'display_image_preview']
    
    def display_image(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.image.url
            )
        return "No image"
    display_image.short_description = "Image"
    
    def display_image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; height: auto; border-radius: 8px;" />',
                obj.image.url
            )
        return "No image"
    display_image_preview.short_description = "Image Preview"

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category__name']
    readonly_fields = ['slug']
    autocomplete_fields = ['category']