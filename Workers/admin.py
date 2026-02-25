from django.contrib import admin
from .models import Worker, WorkExperience

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'category', 'subcategory', 'city', 'created_by', 'phone_number', 'is_verified', 'created_at', 'is_deleted']
    list_filter = ['category', 'subcategory', 'city', 'is_verified', 'is_deleted', 'created_by', 'created_at']
    search_fields = ['full_name', 'phone_number', 'email', 'skills', 'category__name', 'subcategory__name', 'created_by__username', 'created_by__email']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Personal Information', {
            'fields': ('user', 'full_name', 'phone_number', 'email', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('address', 'country', 'state', 'city', 'district', 'region')
        }),
        ('Professional Information', {
            'fields': ('category', 'subcategory', 'years_of_experience', 'skills', 'availability', 'expected_daily_wage')
        }),
        ('Creator Information', {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    ordering = ['-created_at']

@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ['worker', 'company_name', 'job_title', 'start_date', 'end_date', 'is_current']
    list_filter = ['start_date', 'is_current']
    search_fields = ['worker__full_name', 'company_name', 'job_title']
    fieldsets = (
        ('Worker Information', {
            'fields': ('worker',)
        }),
        ('Experience Details', {
            'fields': ('company_name', 'job_title', 'start_date', 'end_date', 'description', 'is_current')
        }),
    )
    ordering = ['-start_date']
