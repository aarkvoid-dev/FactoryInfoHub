from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def image_index(value, total):
    return ((value - 1) % total) + 1