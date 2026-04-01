# home/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import Page

@receiver([post_save, post_delete], sender=Page)
def invalidate_page_cache(sender, **kwargs):
    cache.delete('global_pages')