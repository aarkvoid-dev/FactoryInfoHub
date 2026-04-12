from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from tinymce.models import HTMLField


class SoftDeleteManager(models.Manager):
    """Custom manager that excludes soft-deleted objects by default"""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """Return all objects including soft-deleted ones"""
        return super().get_queryset()

    def deleted_only(self):
        """Return only soft-deleted objects"""
        return super().get_queryset().filter(is_deleted=True)


class SoftDeleteModel(models.Model):
    """Abstract base model with soft delete functionality"""

    is_deleted = models.BooleanField(default=False, help_text="Mark as deleted without removing from database")
    deleted_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp when soft deleted")

    objects = SoftDeleteManager()

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['is_deleted']),
            models.Index(fields=['deleted_at']),
        ]

    def delete(self, using=None, keep_parents=False):
        """Soft delete instead of hard delete"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        """Restore a soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    def hard_delete(self):
        """Permanently delete the object"""
        super(SoftDeleteModel, self).delete()


class SoftDeleteAdminMixin:
    """Mixin for admin classes to handle soft delete"""

    def get_queryset(self, request):
        """Show all objects including soft-deleted ones in admin"""
        return self.model.objects.all_with_deleted()

    def delete_model(self, request, obj):
        """Soft delete instead of hard delete in admin"""
        obj.delete()

    def delete_queryset(self, request, queryset):
        """Soft delete multiple objects"""
        for obj in queryset:
            obj.delete()

    actions = ['restore_selected', 'hard_delete_selected']

    def restore_selected(self, request, queryset):
        """Restore selected soft-deleted objects"""
        count = 0
        for obj in queryset:
            if obj.is_deleted:
                obj.restore()
                count += 1
        self.message_user(request, f'Successfully restored {count} objects.')

    def hard_delete_selected(self, request, queryset):
        """Permanently delete selected objects"""
        count = queryset.count()
        for obj in queryset:
            obj.hard_delete()
        self.message_user(request, f'Permanently deleted {count} objects.')

    def soft_delete_selected(self, request, queryset):
        """Soft delete selected objects"""
        count = 0
        for obj in queryset:
            if not obj.is_deleted:
                obj.delete()
                count += 1
        self.message_user(request, f'Soft deleted {count} objects.')

    restore_selected.short_description = "Restore selected objects"
    hard_delete_selected.short_description = "Permanently delete selected objects"
    soft_delete_selected.short_description = "Soft delete selected objects"


class HomePageVideo(SoftDeleteModel):
    title = models.CharField(max_length=200)
    video = models.FileField(upload_to='home_videos/')
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Enforce constraint: only one active video at a time
        if self.is_active:
            # Deactivate all other active videos
            HomePageVideo.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        # Ensure at least one video is active after save
        super().save(*args, **kwargs)
        
        # Check if this is the only active video and we're deactivating it
        if not self.is_active and not HomePageVideo.objects.filter(is_active=True, is_deleted=False).exists():
            # Reactivate this video to maintain constraint
            self.is_active = True
            super().save(update_fields=['is_active'])

    def clean(self):
        # Additional validation to prevent constraint violations
        if not self.is_active:
            # Check if deactivating this video would leave no active videos
            active_videos = HomePageVideo.objects.filter(is_active=True, is_deleted=False)
            if self.pk:
                active_videos = active_videos.exclude(pk=self.pk)
            
            if not active_videos.exists():
                raise ValidationError('Cannot deactivate the only active video. Activate another video first.')
    
    def delete(self, using=None, keep_parents=False):
        # Check constraint before soft delete
        if self.is_active and HomePageVideo.objects.filter(is_active=True, is_deleted=False).count() <= 1:
            raise ValidationError('Cannot delete the only active video. Add and Activate another video first.')
        super().delete(using, keep_parents)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            *SoftDeleteModel.Meta.indexes,
            models.Index(fields=['is_active']),
        ]


class ContactMessage(SoftDeleteModel):
    """Model to store contact form submissions"""

    INQUIRY_TYPES = (
        ('enquiry', 'General Enquiry'),
        ('export', 'Export Enquiry'),
        ('karigar', 'Any Question related to staff hiring for boutique/brand/karkhana or any Other.'),
        ('online_class', 'Online Class Enquiry'),
    )
    
    type = models.CharField(max_length=20, choices=INQUIRY_TYPES, default='enquiry')
    
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    mobile_number = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        help_text="Contact phone number (optional)"
    )
    subject = models.CharField(max_length=200)
    message = models.TextField()
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="The user who submitted this message (if logged in)"
    )
    brand_name = models.CharField(max_length=200,null=True,blank=True)
    is_read = models.BooleanField(default=False, help_text="Whether the message has been read by admin")
    read_at = models.DateTimeField(null=True, blank=True)
    has_replies = models.BooleanField(default=False, help_text="Whether this message has been replied to")
    last_reply_at = models.DateTimeField(null=True, blank=True, help_text="When the last reply was sent")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

    def mark_as_read(self):
        """Mark this message as read"""
        self.is_read = True
        self.read_at = timezone.now()
        self.save()

    def mark_replied(self):
        """Mark this message as having been replied to"""
        self.has_replies = True
        self.last_reply_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at', '-is_read']
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        indexes = [
            *SoftDeleteModel.Meta.indexes,
            models.Index(fields=['is_read']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user']),
            models.Index(fields=['has_replies']),
            models.Index(fields=['last_reply_at']),
        ]


class ContactReply(SoftDeleteModel):
    """Model to track replies sent to contact messages"""
    contact_message = models.ForeignKey(
        ContactMessage, 
        on_delete=models.CASCADE, 
        related_name='replies',
        help_text="The original contact message this reply is for"
    )
    admin_user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="The admin user who sent this reply"
    )
    subject = models.CharField(max_length=200, help_text="Subject of the reply email")
    message = models.TextField(help_text="Content of the reply message")
    recipient_email = models.EmailField(help_text="Email address the reply was sent to")
    sent_at = models.DateTimeField(default=timezone.now, help_text="When the reply was sent")
    email_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
        ],
        default='pending',
        help_text="Status of the email sending"
    )
    error_message = models.TextField(blank=True, help_text="Error message if email sending failed")

    def __str__(self):
        return f"Reply to {self.contact_message.name} - {self.subject}"

    def mark_as_sent(self):
        """Mark this reply as successfully sent"""
        self.email_status = 'sent'
        self.save()
        # Update the parent contact message
        self.contact_message.mark_replied()

    def mark_as_failed(self, error_message=""):
        """Mark this reply as failed"""
        self.email_status = 'failed'
        self.error_message = error_message
        self.save()

    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Contact Reply"
        verbose_name_plural = "Contact Replies"
        indexes = [
            *SoftDeleteModel.Meta.indexes,
            models.Index(fields=['contact_message']),
            models.Index(fields=['admin_user']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['email_status']),
        ]


class Page(SoftDeleteModel):
    """Model for dynamic pages like Terms & Conditions, Refund Policy, etc."""
    PAGE_TYPES = (
        ('terms', 'Terms & Conditions'),
        ('refund', 'Refund Policy'),
        ('disclaimer', 'Disclaimer'),
        ('privacy', 'Privacy Policy'),
        ('about', 'About Us'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = HTMLField()
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, unique=True)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Order in which pages appear in navigation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    meta_title = models.CharField(max_length=200, blank=True, help_text="SEO meta title")
    meta_description = models.TextField(blank=True, help_text="SEO meta description")
    
    class Meta:
        verbose_name = "Page"
        verbose_name_plural = "Pages"
        ordering = ['order', 'title']
        indexes = [
            *SoftDeleteModel.Meta.indexes,
            models.Index(fields=['page_type']),
            models.Index(fields=['is_published']),
            models.Index(fields=['slug']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('home:page_detail', kwargs={'slug': self.slug})
    
    @classmethod
    def get_page_by_type(cls, page_type):
        """Get a page by its type"""
        try:
            return cls.objects.get(page_type=page_type, is_published=True, is_deleted=False)
        except cls.DoesNotExist:
            return None


class PageSection(SoftDeleteModel):
    """Optional sections within a page for more complex layouts"""
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='sections')
    title = models.CharField(max_length=200, blank=True)
    content = HTMLField()
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
        verbose_name = "Page Section"
        verbose_name_plural = "Page Sections"
        indexes = [
            *SoftDeleteModel.Meta.indexes,
            models.Index(fields=['page']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"{self.page.title} - {self.title or 'Section'}"
