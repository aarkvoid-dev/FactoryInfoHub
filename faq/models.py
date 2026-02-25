"""
FAQ application models.

This module contains the models for the FAQ (Frequently Asked Questions) application,
including Question, Category, and Answer models.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from category.models import Category
from Home.models import SoftDeleteModel



class FAQQuestion(SoftDeleteModel):
    """
    FAQ Question model.
    
    Represents a frequently asked question with its answer and metadata.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    # Question information
    title = models.CharField(max_length=200, help_text="The question text")
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='questions',
        help_text="Category this question belongs to"
    )
    
    # Content
    question_text = models.TextField(help_text="Detailed question description")
    answer_text = models.TextField(help_text="Answer to the question")
    
    # Metadata
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft',
        help_text="Publication status of the question"
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Whether this question should be featured prominently"
    )
    view_count = models.PositiveIntegerField(default=0, help_text="Number of times this question has been viewed")
    
    # SEO and organization
    tags = models.CharField(
        max_length=500, 
        blank=True,
        help_text="Comma-separated tags for search and organization"
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Order for manual sorting within category"
    )
    
    # Audit fields
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_faq_questions'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_faq_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "FAQ Question"
        verbose_name_plural = "FAQ Questions"
        ordering = ['-is_featured', 'order', 'title']
        indexes = [
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['view_count']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('faq:question_detail', kwargs={'slug': self.slug})
    
    def get_tags_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def increment_view_count(self):
        """Increment the view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    @property
    def is_published(self):
        """Check if question is published"""
        return self.status == 'published'
    
    @classmethod
    def get_published_questions(cls):
        """Get all published questions"""
        return cls.objects.filter(status='published')


class FAQFeedback(models.Model):
    """
    User feedback for FAQ questions.
    
    Allows users to rate and provide feedback on FAQ questions.
    """
    RATING_CHOICES = [
        (1, '1 - Very Poor'),
        (2, '2 - Poor'),
        (3, '3 - Average'),
        (4, '4 - Good'),
        (5, '5 - Excellent'),
    ]
    
    question = models.ForeignKey(
        FAQQuestion, 
        on_delete=models.CASCADE, 
        related_name='feedback'
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="User who provided feedback (can be anonymous)"
    )
    rating = models.PositiveIntegerField(
        choices=RATING_CHOICES,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5"
    )
    comment = models.TextField(
        blank=True,
        help_text="Optional comment or suggestion"
    )
    is_helpful = models.BooleanField(
        null=True,
        blank=True,
        help_text="Whether the user found this answer helpful"
    )
    
    # Metadata
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        help_text="IP address of the user (for anonymous feedback)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "FAQ Feedback"
        verbose_name_plural = "FAQ Feedback"
        ordering = ['-created_at']
        unique_together = [['question', 'user']]  # One feedback per user per question
    
    def __str__(self):
        return f"Feedback for {self.question.title} - Rating: {self.rating}"


class FAQSearchLog(models.Model):
    """
    Log of user searches in the FAQ system.
    
    Used for analytics and to identify common search terms.
    """
    search_query = models.CharField(max_length=200, help_text="The search query entered by user")
    search_results_count = models.PositiveIntegerField(default=0, help_text="Number of results found")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "FAQ Search Log"
        verbose_name_plural = "FAQ Search Logs"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Search: '{self.search_query}' - {self.search_results_count} results"