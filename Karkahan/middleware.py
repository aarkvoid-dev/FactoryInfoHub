"""
Factory View Tracking Middleware

This middleware automatically tracks views to factory detail pages with anti-fraud measures.
"""

from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from django.contrib.auth.models import User
from .models import FactoryViewTracker, FactoryViewStats
import hashlib
import logging

logger = logging.getLogger(__name__)


class FactoryViewTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to automatically track factory views with anti-fraud measures.
    """
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process each view request and track factory views if applicable.
        """
        # Only track GET requests to factory detail pages
        if request.method != 'GET':
            return None
        
        # Check if this is a factory detail view
        if hasattr(view_func, '__name__') and view_func.__name__ == 'factory_detail':
            factory_slug = view_kwargs.get('slug')
            if factory_slug:
                self.track_factory_view(request, factory_slug)
        
        return None
    
    def track_factory_view(self, request, factory_slug):
        """
        Track a factory view with anti-fraud measures.
        """
        try:
            from .models import Factory
            
            # Get the factory
            try:
                factory = Factory.objects.get(slug=factory_slug, is_active=True, is_deleted=False)
            except Factory.DoesNotExist:
                return
            
            # Get user information
            user = request.user if request.user.is_authenticated else None
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Generate session identifier for deduplication
            session_id = self.generate_session_id(request, factory_slug)
            
            # Check if view should be tracked
            if not FactoryViewTracker.should_track_view(factory, ip_address, user, session_id):
                return
            
            # Create view tracker record
            view_tracker = FactoryViewTracker.objects.create(
                factory=factory,
                ip_address=ip_address,
                user_agent=user_agent,
                user=user,
                session_id=session_id,
                is_bot=self.is_bot_request(user_agent)
            )
            
            # Update view statistics
            self.update_factory_view_stats(factory)
            
            logger.debug(f"Tracked view for factory {factory.name} by {ip_address}")
            
        except Exception as e:
            logger.error(f"Error tracking factory view: {e}")
    
    def get_client_ip(self, request):
        """
        Get the client IP address from the request.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
        return ip
    
    def generate_session_id(self, request, factory_slug):
        """
        Generate a session identifier for deduplication.
        """
        # Create a unique session identifier based on user session and factory
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        
        # Combine session key with factory slug for uniqueness
        session_data = f"{session_key}_{factory_slug}"
        
        # Hash it for consistency
        return hashlib.md5(session_data.encode()).hexdigest()
    
    def is_bot_request(self, user_agent):
        """
        Check if the request appears to be from a bot.
        """
        if not user_agent:
            return True
        
        # Common bot user agent patterns
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'httpie', 'postman', 'insomnia'
        ]
        
        user_agent_lower = user_agent.lower()
        for pattern in bot_patterns:
            if pattern in user_agent_lower:
                return True
        
        return False
    
    def update_factory_view_stats(self, factory):
        """
        Update the factory's view statistics.
        """
        try:
            # Get or create view stats
            stats, created = FactoryViewStats.objects.get_or_create(factory=factory)
            
            # Update all statistics
            stats.update_all_stats()
            
        except Exception as e:
            logger.error(f"Error updating view stats for factory {factory.name}: {e}")


class ViewStatsCacheMiddleware(MiddlewareMixin):
    """
    Middleware to cache view statistics for better performance.
    """
    
    def process_request(self, request):
        """
        Set up cache for view statistics.
        """
        # This could be extended to implement caching strategies
        # For now, we'll rely on Django's built-in caching
        pass
    
    def process_response(self, request, response):
        """
        Clean up after request processing.
        """
        return response