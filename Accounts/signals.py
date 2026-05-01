# your_app/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile

@receiver(post_save, sender=User)
def set_new_user_inactive(sender, instance, created, **kwargs):
    if created and not instance.is_superuser:
        instance.is_active = False
        instance.save(update_fields=['is_active'])

@receiver(post_save, sender=Profile)
def activate_user_after_email_verified(sender, instance, **kwargs):
    try:
        old = Profile.objects.get(pk=instance.pk)
        was_verified = old.email_verified
    except Profile.DoesNotExist:
        was_verified = False

    if not was_verified and instance.email_verified:
        user = instance.user
        if user and not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])