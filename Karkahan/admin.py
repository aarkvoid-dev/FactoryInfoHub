from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from .models import Factory, FactoryImage, ShoppingCart, FactoryPurchase, PurchaseHistory, Order, OrderItem, Payment
from .forms import OrderStatusForm, RefundForm


class FactoryImageInline(admin.TabularInline):
    model = FactoryImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 100px; height: 100px; object-fit: cover; border-radius: 6px; border: 1px solid #ddd;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'city', 'state', 'price', 'is_active', 'is_verified', 'created_at']
    list_filter = ['category', 'subcategory', 'country', 'state', 'city', 'is_active', 'is_verified']
    search_fields = ['name', 'description', 'address', 'contact_person']
    readonly_fields = ['created_at', 'updated_at', 'slug']
    inlines = [FactoryImageInline]
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'subcategory', 'price')
        }),
        ('Location', {
            'fields': ('country', 'state', 'city', 'district', 'region', 'address', 'pincode')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_phone', 'contact_email', 'website')
        }),
        ('Factory Details', {
            'fields': ('factory_type', 'production_capacity', 'working_hours', 'holidays', 'established_year', 'employee_count', 'annual_turnover')
        }),
        ('Media', {
            'fields': ('video_url',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'created_by')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    actions = ['make_active', 'make_inactive', 'mark_verified', 'mark_unverified']

    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} factories were successfully marked as active.')
    make_active.short_description = "Mark selected factories as active"

    def make_inactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} factories were successfully marked as inactive.')
    make_inactive.short_description = "Mark selected factories as inactive"

    def mark_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} factories were successfully marked as verified.')
    mark_verified.short_description = "Mark selected factories as verified"

    def mark_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} factories were successfully marked as unverified.')
    mark_unverified.short_description = "Mark selected factories as unverified"


@admin.register(FactoryImage)
class FactoryImageAdmin(admin.ModelAdmin):
    list_display = ['factory', 'image_preview', 'alt_text', 'is_primary', 'created_at']
    list_filter = ['is_primary', 'factory']
    search_fields = ['factory__name', 'alt_text']
    readonly_fields = ['image_preview', 'created_at', 'updated_at']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 60px; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ['user', 'factory', 'quantity', 'total_price', 'added_at']
    list_filter = ['added_at', 'factory']
    search_fields = ['user__username', 'factory__name']
    readonly_fields = ['total_price', 'added_at', 'updated_at']

    def total_price(self, obj):
        return f"Rs. {obj.total_price}"
    total_price.short_description = 'Total Price'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'customer_name', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'payment_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'customer_name', 'customer_email']
    readonly_fields = ['order_number', 'created_at', 'updated_at', 'completed_at']
    actions = ['mark_completed', 'mark_cancelled', 'mark_refunded']
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'customer_name', 'customer_email', 'customer_phone')
        }),
        ('Order Details', {
            'fields': ('subtotal', 'tax_amount', 'service_fee', 'total_amount', 'payment_method')
        }),
        ('Status', {
            'fields': ('status', 'payment_status', 'tracking_number', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed', payment_status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} orders were successfully marked as completed.')
    mark_completed.short_description = "Mark selected orders as completed"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled', payment_status='cancelled')
        self.message_user(request, f'{updated} orders were successfully marked as cancelled.')
    mark_cancelled.short_description = "Mark selected orders as cancelled"

    def mark_refunded(self, request, queryset):
        for order in queryset:
            order.status = 'refunded'
            order.payment_status = 'refunded'
            order.save()
            
            # Process refunds for payments
            for payment in order.payments.all():
                payment.status = 'refunded'
                payment.refunded_amount = payment.amount
                payment.refunded_at = timezone.now()
                payment.save()
        
        self.message_user(request, f'{queryset.count()} orders were successfully marked as refunded.')
    mark_refunded.short_description = "Mark selected orders as refunded"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'factory', 'quantity', 'price_at_purchase', 'total_price']
    list_filter = ['order', 'factory']
    search_fields = ['order__order_number', 'factory__name']
    readonly_fields = ['total_price']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'payment_method', 'amount', 'currency', 'status', 'transaction_id', 'created_at']
    list_filter = ['status', 'payment_method', 'currency', 'created_at']
    search_fields = ['order__order_number', 'transaction_id', 'gateway_response']
    readonly_fields = ['transaction_id', 'gateway_response', 'gateway_error', 'completed_at', 'refunded_at']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('order', 'payment_method', 'amount', 'currency', 'transaction_id')
        }),
        ('Status', {
            'fields': ('status', 'refunded_amount', 'refund_reason')
        }),
        ('Gateway Information', {
            'fields': ('gateway_response', 'gateway_error'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at', 'refunded_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_completed', 'mark_failed', 'mark_refunded']

    def mark_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} payments were successfully marked as completed.')
    mark_completed.short_description = "Mark selected payments as completed"

    def mark_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments were successfully marked as failed.')
    mark_failed.short_description = "Mark selected payments as failed"

    def mark_refunded(self, request, queryset):
        for payment in queryset:
            payment.status = 'refunded'
            payment.refunded_amount = payment.amount
            payment.refunded_at = timezone.now()
            payment.save()
        
        self.message_user(request, f'{queryset.count()} payments were successfully marked as refunded.')
    mark_refunded.short_description = "Mark selected payments as refunded"


@admin.register(FactoryPurchase)
class FactoryPurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'factory', 'quantity', 'price_at_purchase', 'payment_status', 'purchased_at']
    list_filter = ['payment_status', 'purchased_at', 'factory']
    search_fields = ['user__username', 'factory__name']
    readonly_fields = ['purchased_at', 'email_sent_at']
    actions = ['mark_completed', 'mark_failed', 'mark_cancelled']

    def mark_completed(self, request, queryset):
        updated = queryset.update(payment_status='completed')
        for purchase in queryset:
            purchase.send_factory_details_email()
        self.message_user(request, f'{updated} purchases were successfully marked as completed.')
    mark_completed.short_description = "Mark selected purchases as completed"

    def mark_failed(self, request, queryset):
        updated = queryset.update(payment_status='failed')
        self.message_user(request, f'{updated} purchases were successfully marked as failed.')
    mark_failed.short_description = "Mark selected purchases as failed"

    def mark_cancelled(self, request, queryset):
        updated = queryset.update(payment_status='cancelled')
        self.message_user(request, f'{updated} purchases were successfully marked as cancelled.')
    mark_cancelled.short_description = "Mark selected purchases as cancelled"


@admin.register(PurchaseHistory)
class PurchaseHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'factory_name', 'purchase_price', 'purchase_quantity', 'purchase_date', 'email_delivered']
    list_filter = ['purchase_date', 'email_delivered']
    search_fields = ['user__username', 'factory_name', 'factory_contact_email']
    readonly_fields = ['purchase_date', 'email_delivered_at']