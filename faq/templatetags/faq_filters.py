from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter
def highlight(text, query):
    """
    Highlight search query terms in text by wrapping them in <mark> tags.
    """
    if not query or not text:
        return text
    
    # Escape HTML to prevent XSS
    text = escape(str(text))
    query = escape(str(query))
    
    # Create a case-insensitive regex pattern
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    
    # Replace matches with highlighted version
    highlighted_text = pattern.sub(r'<mark>\g<0></mark>', text)
    
    # Mark as safe HTML
    return mark_safe(highlighted_text)

@register.filter
def get_tags_list(question):
    """
    Get list of tags from question's tags field.
    """
    if hasattr(question, 'tags') and question.tags:
        return [tag.strip() for tag in question.tags.split(',') if tag.strip()]
    return []

@register.filter
def question_count_by_category(category):
    """
    Get the count of published questions in a category.
    """
    return category.questions.filter(is_published=True).count()

@register.filter
def truncatechars_middle(text, max_length):
    """
    Truncate text in the middle, keeping beginning and end.
    """
    if len(text) <= max_length:
        return text
    
    # Calculate how much to show from beginning and end
    chars_per_side = (max_length - 3) // 2
    start = text[:chars_per_side]
    end = text[-chars_per_side:]
    
    return f"{start}...{end}"

@register.filter
def format_date_range(start_date, end_date):
    """
    Format date range for display.
    """
    if start_date and end_date:
        if start_date == end_date:
            return start_date.strftime('%B %d, %Y')
        else:
            return f"{start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}"
    elif start_date:
        return start_date.strftime('%B %d, %Y')
    return ""