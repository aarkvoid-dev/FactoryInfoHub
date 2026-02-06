from django.db import models
from django.utils import timezone


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
