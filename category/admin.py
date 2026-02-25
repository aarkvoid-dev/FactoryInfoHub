from django.contrib import admin
from .models import Category, SubCategory

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['slug']

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'slug', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'category__name']
    readonly_fields = ['slug']
    autocomplete_fields = ['category']