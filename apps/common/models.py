"""Shared abstract models for TRAUCK.

Provides TimeStampedModel used by domain apps. Kept minimal and abstract.
"""
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model with created/updated timestamps.

    Fields
    - created_at: auto-set on create
    - updated_at: auto-updated on save
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
