"""
FAQ application configuration.

This module contains the Django app configuration for the FAQ application.
"""

from django.apps import AppConfig


class FaqConfig(AppConfig):
    """FAQ application configuration."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'faq'
    verbose_name = 'FAQ (Frequently Asked Questions)'
    
    def ready(self):
        """
        Import signal handlers when the app is ready.
        
        This method is called when the Django application is loaded.
        """
        try:
            import faq.signals  # noqa: F401
        except ImportError:
            pass