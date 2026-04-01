from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.html import format_html
from django.db import transaction
from django.http import HttpResponse
import logging

from .models import Factory, FactoryImage, Cart, CartItem, Order, OrderItem, PaymentGateway, FactoryViewTracker, FactoryViewStats
from .views import send_order_receipt

logger = logging.getLogger(__name__)

class FactoryImageInline(admin.TabularInline):
    model = FactoryImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'image_tag']
    readonly_fields = ['image_tag']

    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" height="80" style="border-radius: 6px;" />', obj.image.url)
        return "No image"
    image_tag.short_description = 'Preview'


@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'city', 'state', 'country', 'price', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'category', 'country', 'state', 'city']
    search_fields = ['name', 'description', 'address', 'contact_person']
    readonly_fields = ['created_at', 'updated_at', 'get_primary_image']
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
            'fields': ('video_url', 'get_primary_image')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'created_by', 'created_at', 'updated_at')
        }),
    )
    prepopulated_fields = {'slug': ('name',)}
    
    def get_primary_image(self, obj):
        if obj.get_primary_image():
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 6px;" />', obj.get_primary_image())
        return "No primary image"
    get_primary_image.short_description = 'Primary Image'


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_price', 'total_items', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def total_items(self, obj):
        return obj.items.count()
    total_items.short_description = 'Items Count'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'factory', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__username', 'factory__name']


@admin.register(PaymentGateway)
class PaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'mode', 'created_at']
    list_filter = ['is_active', 'mode', 'name']
    search_fields = ['name']
    
    def save_model(self, request, obj, form, change):
        if obj.is_active:
            # Deactivate all other gateways
            PaymentGateway.objects.exclude(pk=obj.pk).update(is_active=False)
        super().save_model(request, obj, form, change)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['factory_name', 'price_at_purchase']
    
    def factory_name(self, obj):
        return obj.factory.name
    factory_name.short_description = 'Factory'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total_amount', 'payment_status', 'payment_method', 'gateway_used', 'order_date', 'receipt_sent']
    list_filter = ['payment_status', 'payment_method', 'gateway_used', 'order_date', 'receipt_sent']
    search_fields = ['user__username', 'user__email', 'transaction_id']
    readonly_fields = ['order_date', 'transaction_id', 'stripe_payment_intent']
    inlines = [OrderItemInline]
    actions = ['mark_as_completed', 'resend_receipt']
    
    def mark_as_completed(self, request, queryset):
        """Admin action to manually mark orders as completed"""
        updated = 0
        for order in queryset:
            if order.payment_status != 'completed':
                order.payment_status = 'completed'
                order.save()
                
                # Clear cart and send email
                try:
                    cart = Cart.objects.get(user=order.user)
                    cart.items.all().delete()
                    
                    factories = [item.factory for item in order.items.all()]
                    send_order_receipt(order.user, order, factories)
                    
                    updated += 1
                except Exception as e:
                    logger.error(f"Error processing order {order.id}: {str(e)}")
        
        if updated > 0:
            messages.success(request, f'Successfully marked {updated} orders as completed and sent receipts.')
        else:
            messages.info(request, 'No orders were updated (already completed).')
    
    mark_as_completed.short_description = "Mark selected orders as completed"
    
    def resend_receipt(self, request, queryset):
        """Admin action to resend order receipts"""
        sent = 0
        failed = 0
        
        for order in queryset:
            try:
                factories = [item.factory for item in order.items.all()]
                if send_order_receipt(order.user, order, factories):
                    sent += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error resending receipt for order {order.id}: {str(e)}")
                failed += 1
        
        if sent > 0:
            messages.success(request, f'Successfully sent {sent} receipts.')
        if failed > 0:
            messages.error(request, f'Failed to send {failed} receipts.')
    
    resend_receipt.short_description = "Resend receipt for selected orders"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'factory', 'price_at_purchase']
    list_filter = ['order__order_date']
    search_fields = ['order__user__username', 'factory__name']


# Custom admin views for payment monitoring
class PaymentAdminSite(admin.AdminSite):
    site_header = 'Factory InfoHub Payment Administration'
    site_title = 'Payment Admin'
    index_title = 'Payment System Monitoring'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('payment-dashboard/', self.admin_view(self.payment_dashboard), name='payment_dashboard'),
            path('fix-order/<int:order_id>/', self.admin_view(self.fix_order), name='fix_order'),
        ]
        return custom_urls + urls

    def payment_dashboard(self, request):
        """Custom admin dashboard for payment monitoring"""
        orders = Order.objects.all().order_by('-order_date')[:50]
        
        # Payment status summary
        total_orders = Order.objects.count()
        completed_orders = Order.objects.filter(payment_status='completed').count()
        pending_orders = Order.objects.filter(payment_status='pending').count()
        failed_orders = Order.objects.filter(payment_status='failed').count()
        
        # Recent failed orders
        recent_failed_orders = Order.objects.filter(payment_status='failed').order_by('-order_date')[:10]
        
        context = {
            **self.each_context(request),
            'orders': orders,
            'total_orders': total_orders,
            'completed_orders': completed_orders,
            'pending_orders': pending_orders,
            'failed_orders': failed_orders,
            'recent_failed_orders': recent_failed_orders,
        }
        
        return render(request, 'admin/payment_dashboard.html', context)

    def fix_order(self, request, order_id):
        """Manual order completion tool"""
        order = get_object_or_404(Order, id=order_id)
        
        if request.method == 'POST':
            try:
                with transaction.atomic():
                    # Mark order as completed
                    order.payment_status = 'completed'
                    order.save()
                    
                    # Clear cart
                    cart = Cart.objects.get(user=order.user)
                    cart.items.all().delete()
                    
                    # Send receipt
                    factories = [item.factory for item in order.items.all()]
                    send_order_receipt(order.user, order, factories)
                    
                    messages.success(request, f'Order {order.id} has been successfully completed.')
                    return redirect('admin:karkahan_order_changelist')
                    
            except Exception as e:
                messages.error(request, f'Error processing order: {str(e)}')
        
        context = {
            **self.each_context(request),
            'order': order,
        }
        return render(request, 'admin/fix_order.html', context)

# Create the custom admin site instance
payment_admin_site = PaymentAdminSite(name='payment_admin')

# Register models with the custom admin site
payment_admin_site.register(Factory, FactoryAdmin)
payment_admin_site.register(Cart, CartAdmin)
payment_admin_site.register(CartItem, CartItemAdmin)
payment_admin_site.register(Order, OrderAdmin)
payment_admin_site.register(OrderItem, OrderItemAdmin)
payment_admin_site.register(PaymentGateway, PaymentGatewayAdmin)

@admin.register(FactoryViewTracker)
class FactoryViewTrackerAdmin(admin.ModelAdmin):
    list_display = ['factory', 'ip_address', 'user', 'viewed_at']
    list_filter = ['viewed_at', 'factory']
    search_fields = ['ip_address', 'factory__name']

    def has_add_permission(self, request):
        return False  # Disable adding new records via admin

    def has_change_permission(self, request, obj=None):
        return False  # Disable editing existing records

    def has_delete_permission(self, request, obj=None):
        return False  # Disable deleting records
    
@admin.register(FactoryViewStats)
class FactoryViewStatsAdmin(admin.ModelAdmin):
    list_display = ['factory', 'total_views', 'today_views', 'weekly_views', 'monthly_views', 'last_updated']
    readonly_fields = ['total_views', 'today_views', 'weekly_views', 'monthly_views', 'last_updated']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
