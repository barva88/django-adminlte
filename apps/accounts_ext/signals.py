"""Signals for accounts_ext: create UserProfile on user creation.

This module is imported in AppConfig.ready() when the app is enabled.
"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth import get_user_model

from .models import UserProfile


@receiver(post_save, sender=get_user_model())
def ensure_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new user is created (if missing).

    This is intentionally tolerant: it will not raise if the profile exists.
    """
    if created:
        UserProfile.objects.get_or_create(user=instance)
