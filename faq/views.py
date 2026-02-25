"""
FAQ application views.

This module contains all the view functions for the FAQ application,
including question listing, search, detail views, and feedback handling.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from .models import FAQQuestion, FAQFeedback, FAQSearchLog
from category.models import Category


def faq_home(request):
    """
    FAQ home page view.
    
    Displays featured questions, categories, and recent questions.
    """
    # Get featured questions
    featured_questions = FAQQuestion.objects.filter(
        status='published', 
        is_featured=True
    ).select_related('category')[:6]
    
    # Get all active categories with question counts
    categories = Category.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__status='published'))
    ).filter(question_count__gt=0).order_by('name')
    
    # Get recent questions
    recent_questions = FAQQuestion.objects.filter(
        status='published'
    ).select_related('category').order_by('-created_at')[:8]
    
    context = {
        'featured_questions': featured_questions,
        'categories': categories,
        'recent_questions': recent_questions,
        'total_questions': FAQQuestion.objects.filter(status='published').count(),
    }
    
    return render(request, 'faq/home.html', context)


def faq_question_detail(request, slug):
    """
    FAQ question detail view.
    
    Displays a single question with its answer and allows feedback.
    """
    question = get_object_or_404(FAQQuestion, slug=slug, status='published')
    
    # Increment view count
    question.increment_view_count()
    
    # Get related questions (same category, excluding current)
    related_questions = FAQQuestion.objects.filter(
        category=question.category,
        status='published'
    ).exclude(pk=question.pk).order_by('-is_featured', '-view_count')[:3]
    
    # Get feedback for this question
    feedback = question.feedback.all().select_related('user').order_by('-created_at')[:5]
    
    # Calculate average rating
    avg_rating = question.feedback.aggregate(avg_rating=Avg('rating'))['avg_rating']
    
    context = {
        'question': question,
        'related_questions': related_questions,
        'feedback': feedback,
        'avg_rating': avg_rating,
    }
    
    return render(request, 'faq/question_detail.html', context)


def faq_search(request):
    """
    FAQ search view.
    
    Handles search queries and displays results with pagination.
    """
    query = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '')
    
    if query:
        # Log the search
        FAQSearchLog.objects.create(
            search_query=query,
            ip_address=get_client_ip(request),
            user=request.user if request.user.is_authenticated else None
        )
    
    # Build search queryset
    if query:
        questions = FAQQuestion.objects.filter(status='published').filter(
            Q(title__icontains=query) |
            Q(question_text__icontains=query) |
            Q(answer_text__icontains=query) |
            Q(tags__icontains=query)
        ).select_related('category').distinct()
    else:
        questions = FAQQuestion.objects.none()
    
    # Apply category filter if specified
    if category_filter:
        questions = questions.filter(category__slug=category_filter)
    
    # Get all categories for filter dropdown
    categories = Category.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__status='published'))
    ).filter(question_count__gt=0)
    
    # Pagination
    paginator = Paginator(questions, 10)
    page = request.GET.get('page')
    
    try:
        questions_page = paginator.page(page)
    except PageNotAnInteger:
        questions_page = paginator.page(1)
    except EmptyPage:
        questions_page = paginator.page(paginator.num_pages)
    
    context = {
        'query': query,
        'questions': questions_page,
        'categories': categories,
        'category_filter': category_filter,
        'total_results': questions.count(),
    }
    
    return render(request, 'faq/search.html', context)


@login_required
@require_POST
def submit_feedback(request, question_slug):
    """
    Submit feedback for a question.
    
    AJAX endpoint for submitting rating and feedback.
    """
    question = get_object_or_404(FAQQuestion, slug=question_slug, status='published')
    
    # Check if user already provided feedback for this question
    existing_feedback = FAQFeedback.objects.filter(
        question=question, 
        user=request.user
    ).first()
    
    if existing_feedback:
        messages.error(request, 'You have already provided feedback for this question.')
        return redirect('faq:question_detail', slug=question_slug)
    
    # Get form data
    rating = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()
    is_helpful = request.POST.get('is_helpful')
    
    # Validate rating
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except (ValueError, TypeError):
        return HttpResponseBadRequest('Invalid rating')
    
    # Create feedback
    feedback = FAQFeedback.objects.create(
        question=question,
        user=request.user,
        rating=rating,
        comment=comment,
        is_helpful=is_helpful == 'true',
        ip_address=get_client_ip(request)
    )
    
    messages.success(request, 'Thank you for your feedback!')
    return redirect('faq:question_detail', slug=question_slug)


def faq_all_questions(request):
    """
    View all FAQ questions.
    
    Displays all published questions with filtering and sorting options.
    """
    # Get filter and sort parameters
    category_filter = request.GET.get('category', '')
    status_filter = request.GET.get('status', 'published')
    sort_by = request.GET.get('sort', 'title')
    
    # Build queryset
    questions = FAQQuestion.objects.filter(status='published').select_related('category')
    
    # Apply category filter
    if category_filter:
        questions = questions.filter(category__slug=category_filter)
    
    # Apply sorting
    sort_options = {
        'title': 'title',
        'category': 'category__name',
        'date': '-created_at',
        'views': '-view_count',
        'rating': '-avg_rating',
    }
    
    if sort_by in sort_options:
        if sort_by == 'rating':
            # For rating, we need to annotate with average rating
            questions = questions.annotate(
                avg_rating=Avg('feedback__rating')
            ).order_by('-avg_rating', 'title')
        else:
            questions = questions.order_by(sort_options[sort_by])
    
    # Pagination
    paginator = Paginator(questions, 15)
    page = request.GET.get('page')
    
    try:
        questions_page = paginator.page(page)
    except PageNotAnInteger:
        questions_page = paginator.page(1)
    except EmptyPage:
        questions_page = paginator.page(paginator.num_pages)
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__status='published'))
    ).filter(question_count__gt=0)
    
    context = {
        'questions': questions_page,
        'categories': categories,
        'category_filter': category_filter,
        'sort_by': sort_by,
    }
    
    return render(request, 'faq/all_questions.html', context)


def faq_statistics(request):
    """
    FAQ statistics view for admins.
    
    Displays analytics and statistics about FAQ usage.
    """
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to view statistics.')
        return redirect('faq:home')
    
    # Basic statistics
    total_questions = FAQQuestion.objects.filter(status='published').count()
    total_categories = Category.objects.filter(is_active=True).count()
    total_feedback = FAQFeedback.objects.count()
    total_searches = FAQSearchLog.objects.count()
    
    # Top questions by views
    top_questions = FAQQuestion.objects.filter(status='published').order_by('-view_count')[:10]
    
    # Top categories by question count
    top_categories = Category.objects.filter(is_active=True).annotate(
        question_count=Count('questions', filter=Q(questions__status='published'))
    ).filter(question_count__gt=0).order_by('-question_count')[:10]
    
    # Recent searches
    recent_searches = FAQSearchLog.objects.order_by('-created_at')[:20]
    
    # Feedback statistics
    feedback_stats = FAQFeedback.objects.aggregate(
        avg_rating=Avg('rating'),
        helpful_count=Count('id', filter=Q(is_helpful=True)),
        not_helpful_count=Count('id', filter=Q(is_helpful=False))
    )
    
    context = {
        'total_questions': total_questions,
        'total_categories': total_categories,
        'total_feedback': total_feedback,
        'total_searches': total_searches,
        'top_questions': top_questions,
        'top_categories': top_categories,
        'recent_searches': recent_searches,
        'feedback_stats': feedback_stats,
    }
    
    return render(request, 'faq/statistics.html', context)


def get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip