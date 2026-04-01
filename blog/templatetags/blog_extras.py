from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def render_blog_content(content, images):
    """
    Render blog content with inline images.
    
    This filter processes blog content and replaces image placeholders
    with actual image HTML, allowing for inline image placement within
    blog content.
    
    Args:
        content (str): The blog post content
        images (QuerySet): BlogImage queryset for this post
    
    Returns:
        str: HTML content with images rendered inline
    """
    if not content:
        return ''
    
    # Convert line breaks to HTML
    html_content = content.replace('\n', '<br>')
    
    # Pattern to match image placeholders like [image:1] or [image:featured]
    image_pattern = r'\[image:(\d+|featured)\]'
    
    def replace_image_placeholder(match):
        image_ref = match.group(1)
        
        if image_ref == 'featured':
            # Get featured image
            image_obj = images.filter(is_featured=True).first()
        else:
            # Get image by order number
            try:
                order = int(image_ref)
                image_obj = images.filter(order=order).first()
            except ValueError:
                return match.group(0)  # Return original if invalid
        
        if image_obj:
            caption_html = f'<div class="mt-2 text-muted text-center text-sm">{image_obj.caption}</div>' if image_obj.caption else ''
            # Handle case where no actual image file exists (e.g., in tests)
            try:
                image_url = image_obj.image.url
            except ValueError:
                # Fallback to a placeholder image if no file is uploaded
                image_url = '/static/img/hero/1.png'
            return f'''
                <div class="blog-image-wrapper my-4 text-center">
                    <img src="{image_url}" alt="{image_obj.caption or 'Blog Image'}" class="img-fluid rounded" style="max-width: 100%; height: auto;">
                    {caption_html}
                </div>
            '''
        else:
            return match.group(0)  # Return original placeholder if image not found
    
    # Replace image placeholders with actual images
    html_content = re.sub(image_pattern, replace_image_placeholder, html_content)
    
    return mark_safe(html_content)


@register.filter
def get_image_by_order(images, order):
    """
    Get a specific image by its order number.
    
    Args:
        images (QuerySet): BlogImage queryset
        order (int): Order number of the image
    
    Returns:
        BlogImage or None: The image object if found
    """
    try:
        return images.filter(order=order).first()
    except:
        return None


@register.filter
def get_featured_image(images):
    """
    Get the featured image from a queryset.
    
    Args:
        images (QuerySet): BlogImage queryset
    
    Returns:
        BlogImage or None: The featured image if found
    """
    return images.filter(is_featured=True).first()