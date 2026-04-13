from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import BlogImage

@receiver([post_save, post_delete], sender=BlogImage)
def ensure_featured_image(sender, instance, **kwargs):
    blog = instance.blog_post
    # Only proceed if the blog has at least one image
    if blog.images.exists():
        featured = blog.images.filter(is_featured=True).first()
        if not featured:
            # No featured image – set the first image (lowest order) as featured
            first_image = blog.images.order_by('order').first()
            first_image.is_featured = True
            # Use update_fields to avoid triggering the signal again
            first_image.save(update_fields=['is_featured'])