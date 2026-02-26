from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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
        super().delete()


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
    created_at = models.DateTimeField(auto_now_add=True)
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
            raise ValidationError('Cannot delete the only active video. Activate another video first.')
        super().delete(using, keep_parents)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            *SoftDeleteModel.Meta.indexes,
            models.Index(fields=['is_active']),
        ]


class ContactMessage(SoftDeleteModel):
    """Model to store contact form submissions"""
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="The user who submitted this message (if logged in)"
    )
    is_read = models.BooleanField(default=False, help_text="Whether the message has been read by admin")
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"

    def mark_as_read(self):
        """Mark this message as read"""
        self.is_read = True
        self.read_at = timezone.now()
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
        ]
