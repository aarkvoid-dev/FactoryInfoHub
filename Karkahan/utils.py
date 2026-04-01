"""
Utility functions for Factory InfoHub
"""
import logging
from django.utils import timezone
from django.http import HttpRequest
from .models import FactoryViewTracker, FactoryViewStats

logger = logging.getLogger(__name__)


def get_client_ip(request: HttpRequest) -> str:
    """Get the client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def track_factory_view(factory, request: HttpRequest, view_timeout_minutes: int = 15):
    """
    Track a factory view with duplicate prevention
    
    Args:
        factory: Factory instance
        request: Django HttpRequest
        view_timeout_minutes: Time window to prevent duplicate views from same IP (default: 15 minutes)
    
    Returns:
        bool: True if view was tracked, False if duplicate was prevented
    """
    try:
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user if request.user.is_authenticated else None
        
        # Check for recent view from same IP to prevent spam
        recent_window = timezone.now() - timezone.timedelta(minutes=view_timeout_minutes)
        recent_views = FactoryViewTracker.objects.filter(
            factory=factory,
            ip_address=ip_address,
            viewed_at__gte=recent_window
        )
        
        if not recent_views.exists():
            # Create new view tracker
            view_tracker = FactoryViewTracker.objects.create(
                factory=factory,
                ip_address=ip_address,
                user_agent=user_agent,
                user=user
            )
            
            # Update aggregated stats
            stats, created = FactoryViewStats.objects.get_or_create(
                factory=factory
            )
            stats.increment_views()
            
            logger.info(f"Factory view tracked: {factory.name} (IP: {ip_address}, User: {user.username if user else 'Anonymous'})")
            return True
        else:
            logger.debug(f"Duplicate factory view prevented: {factory.name} (IP: {ip_address})")
            return False
            
    except Exception as e:
        logger.error(f"Error tracking factory view for {factory.name}: {e}")
        return False


def get_factory_view_stats(factory):
    """
    Get view statistics for a factory
    
    Args:
        factory: Factory instance
    
    Returns:
        dict: View statistics
    """
    try:
        stats, created = FactoryViewStats.objects.get_or_create(factory=factory)
        
        return {
            'total_views': stats.total_views,
            'today_views': stats.today_views,
            'weekly_views': stats.weekly_views,
            'monthly_views': stats.monthly_views,
            'last_updated': stats.last_updated,
        }
    except Exception as e:
        logger.error(f"Error getting view stats for factory {factory.name}: {e}")
        return {
            'total_views': 0,
            'today_views': 0,
            'weekly_views': 0,
            'monthly_views': 0,
            'last_updated': None,
        }


def update_all_view_stats():
    """
    Update all factory view statistics (for management commands)
    
    Returns:
        int: Number of factories updated
    """
    updated_count = 0
    try:
        factories = FactoryViewStats.objects.select_related('factory').all()
        
        for stats in factories:
            stats.update_all_stats()
            updated_count += 1
            
        logger.info(f"Updated view stats for {updated_count} factories")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error updating view stats: {e}")
        return updated_count


def get_top_viewed_factories(limit: int = 10):
    """
    Get top viewed factories
    
    Args:
        limit: Number of factories to return
    
    Returns:
        QuerySet: Top viewed factories with stats
    """
    try:
        from .models import Factory
        
        return Factory.objects.filter(
            is_active=True,
            is_deleted=False,
            view_stats__isnull=False
        ).select_related('view_stats').order_by('-view_stats__total_views')[:limit]
        
    except Exception as e:
        logger.error(f"Error getting top viewed factories: {e}")
        return Factory.objects.none()


def get_view_analytics_summary():
    """
    Get overall view analytics summary
    
    Returns:
        dict: Analytics summary
    """
    try:
        from django.db.models import Sum, Count
        from .models import Factory
        
        total_factories = Factory.objects.filter(is_deleted=False).count()
        active_factories = Factory.objects.filter(is_active=True, is_deleted=False).count()
        
        # View statistics
        view_stats = FactoryViewStats.objects.aggregate(
            total_views=Sum('total_views'),
            today_views=Sum('today_views'),
            weekly_views=Sum('weekly_views'),
            monthly_views=Sum('monthly_views'),
            factories_with_views=Count('factory')
        )
        
        # Most viewed factory
        most_viewed = FactoryViewStats.objects.select_related('factory').order_by('-total_views').first()
        
        return {
            'total_factories': total_factories,
            'active_factories': active_factories,
            'factories_with_views': view_stats.get('factories_with_views', 0),
            'total_views': view_stats.get('total_views', 0) or 0,
            'today_views': view_stats.get('today_views', 0) or 0,
            'weekly_views': view_stats.get('weekly_views', 0) or 0,
            'monthly_views': view_stats.get('monthly_views', 0) or 0,
            'most_viewed_factory': most_viewed.factory if most_viewed else None,
            'most_viewed_count': most_viewed.total_views if most_viewed else 0,
        }
        
    except Exception as e:
        logger.error(f"Error getting view analytics summary: {e}")
        return {
            'total_factories': 0,
            'active_factories': 0,
            'factories_with_views': 0,
            'total_views': 0,
            'today_views': 0,
            'weekly_views': 0,
            'monthly_views': 0,
            'most_viewed_factory': None,
            'most_viewed_count': 0,
        }