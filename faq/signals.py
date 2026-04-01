"""
FAQ application signals.

This module contains Django signals for the FAQ application.
"""

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import FAQ

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FAQ)
def faq_post_save_handler(sender, instance, created, **kwargs):
    """
    Handle actions after FAQ is saved.
    
    Args:
        sender: The model class
        instance: The FAQ instance
        created: Boolean indicating if this is a new instance
        **kwargs: Additional keyword arguments
    """
    if created:
        logger.info(f"New FAQ created: {instance.question} (ID: {instance.id})")
    else:
        logger.info(f"FAQ updated: {instance.question} (ID: {instance.id})")


@receiver(pre_delete, sender=FAQ)
def faq_pre_delete_handler(sender, instance, **kwargs):
    """
    Handle actions before FAQ is deleted.
    
    Args:
        sender: The model class
        instance: The FAQ instance being deleted
        **kwargs: Additional keyword arguments
    """
    logger.info(f"FAQ marked for deletion: {instance.question} (ID: {instance.id})")


@receiver(post_save, sender=FAQ)
def faq_status_change_handler(sender, instance, **kwargs):
    """
    Handle FAQ status changes.
    
    Args:
        sender: The model class
        instance: The FAQ instance
        **kwargs: Additional keyword arguments
    """
    # Log status changes
    if hasattr(instance, '_original_status') and instance._original_status != instance.status:
        logger.info(
            f"FAQ status changed: {instance.question} "
            f"(ID: {instance.id}) - {instance._original_status} -> {instance.status}"
        )


def update_faq_search_index(faq_instance):
    """
    Update search index for FAQ instance.
    
    This is a placeholder function that could be used to update
    search indexes when FAQ content changes.
    
    Args:
        faq_instance: The FAQ instance to index
    """
    # This would typically integrate with a search backend like Elasticsearch
    # or update a full-text search index
    pass


def invalidate_faq_cache(faq_instance):
    """
    Invalidate cached FAQ data.
    
    This is a placeholder function that could be used to clear
    cached FAQ data when content changes.
    
    Args:
        faq_instance: The FAQ instance that changed
    """
    # This would typically clear cached data from Redis, Memcached, etc.
    pass