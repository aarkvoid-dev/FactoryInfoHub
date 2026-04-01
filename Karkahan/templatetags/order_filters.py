from django import template

register = template.Library()

@register.filter
def completed_orders_count(orders):
    """Count completed orders from a queryset"""
    return orders.filter(payment_status='completed').count()

@register.filter
def sum_total(queryset, field_name):
    """Sum a field across a queryset"""
    return sum(getattr(item, field_name, 0) for item in queryset)

@register.filter
def total_spent(orders):
    """Calculate total amount spent from orders queryset"""
    return sum(order.total_amount for order in orders if order.total_amount)
