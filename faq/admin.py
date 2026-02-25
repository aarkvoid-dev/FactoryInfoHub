"""
FAQ application admin interface.

This module contains the admin configuration for the FAQ application,
providing an intuitive interface for managing FAQ questions, categories,
and feedback.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django import forms
from .models import FAQQuestion, FAQFeedback, FAQSearchLog


class FAQQuestionAdminForm(forms.ModelForm):
    """Custom form for FAQQuestion admin with enhanced widgets."""
    
    class Meta:
        model = FAQQuestion
        fields = '__all__'
        widgets = {
            'question_text': forms.Textarea(attrs={'rows': 4, 'cols': 80}),
            'answer_text': forms.Textarea(attrs={'rows': 10, 'cols': 80}),
            'tags': forms.TextInput(attrs={'placeholder': 'tag1, tag2, tag3'}),
        }



@admin.register(FAQQuestion)
class FAQQuestionAdmin(admin.ModelAdmin):
    """Admin interface for FAQ questions."""
    
    form = FAQQuestionAdminForm
    
    list_display = [
        'title', 'category', 'status', 'is_featured', 
        'view_count', 'created_at', 'created_by'
    ]
    list_filter = [
        'status', 'is_featured', 'category', 'created_at', 
        'created_by'
    ]
    search_fields = ['title', 'question_text', 'answer_text', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'view_count', 'url_preview']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'category', 'status'),
        }),
        ('Content', {
            'fields': ('question_text', 'answer_text'),
        }),
        ('Organization', {
            'fields': ('is_featured', 'order', 'tags'),
            'classes': ('collapse',),
        }),
        ('SEO & Analytics', {
            'fields': ('view_count', 'url_preview'),
            'classes': ('collapse',),
        }),
        ('Audit', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    actions = ['make_published', 'make_draft', 'make_archived', 'mark_as_featured']
    
    def save_model(self, request, obj, form, change):
        """Set created_by or updated_by fields."""
        if not change:  # New object
            obj.created_by = request.user
        else:  # Existing object
            obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def make_published(self, request, queryset):
        """Mark selected questions as published."""
        updated = queryset.update(status='published')
        self.message_user(request, f'{updated} questions were successfully marked as published.')
    make_published.short_description = "Mark selected questions as published"
    
    def make_draft(self, request, queryset):
        """Mark selected questions as draft."""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} questions were successfully marked as draft.')
    make_draft.short_description = "Mark selected questions as draft"
    
    def make_archived(self, request, queryset):
        """Mark selected questions as archived."""
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} questions were successfully marked as archived.')
    make_archived.short_description = "Mark selected questions as archived"
    
    def mark_as_featured(self, request, queryset):
        """Mark selected questions as featured."""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} questions were successfully marked as featured.')
    mark_as_featured.short_description = "Mark selected questions as featured"
    
    def url_preview(self, obj):
        """Display a preview of the question URL."""
        if obj.pk:
            url = obj.get_absolute_url()
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "Save to see URL"
    url_preview.short_description = "URL Preview"
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('category', 'created_by', 'updated_by')


@admin.register(FAQFeedback)
class FAQFeedbackAdmin(admin.ModelAdmin):
    """Admin interface for FAQ feedback."""
    
    list_display = [
        'question', 'rating', 'is_helpful', 'user', 'created_at'
    ]
    list_filter = ['rating', 'is_helpful', 'created_at', 'question']
    search_fields = ['question__title', 'comment', 'user__username']
    readonly_fields = ['created_at', 'ip_address']
    
    fieldsets = (
        (None, {
            'fields': ('question', 'user', 'rating'),
        }),
        ('Feedback', {
            'fields': ('comment', 'is_helpful'),
        }),
        ('Metadata', {
            'fields': ('ip_address', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('question', 'user')


@admin.register(FAQSearchLog)
class FAQSearchLogAdmin(admin.ModelAdmin):
    """Admin interface for FAQ search logs."""
    
    list_display = [
        'search_query', 'search_results_count', 'user', 'ip_address', 'created_at'
    ]
    list_filter = ['created_at', 'search_results_count']
    search_fields = ['search_query', 'user__username', 'ip_address']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('search_query', 'search_results_count'),
        }),
        ('User Information', {
            'fields': ('user', 'ip_address'),
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding search logs manually."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable editing search logs."""
        return False
    
    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related('user')