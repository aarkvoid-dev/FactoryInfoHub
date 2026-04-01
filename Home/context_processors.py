# home/context_processors.py
from django.core.cache import cache
from .models import Page

def global_pages(request):
    # Try to fetch from cache first
    pages = cache.get('global_pages')
    if pages is None:
        # Not in cache, run the query
        pages = Page.objects.filter(is_published=True, is_deleted=False).order_by('order', 'title')
        # Store in cache for 15 minutes (900 seconds)
        cache.set('global_pages', pages, 900)
    return {'pages': pages}