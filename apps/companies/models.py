"""Company models (complement) if the models module is not present.

This file mirrors the migration definition and allows imports when the app is enabled.
"""
from django.conf import settings
from django.db import models
from django.db.models import Index
from apps.common.models import TimeStampedModel


class CompanyType(models.TextChoices):
    OWNER_OPERATOR = "owner_operator", "Owner-Operator"
    SMALL_FLEET = "small_fleet", "Small Fleet"
    DISPATCHER = "dispatcher", "Dispatcher"


class Company(TimeStampedModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='owned_companies')
    name = models.CharField(max_length=160)
    dot = models.CharField(max_length=32, blank=True)
    mc = models.CharField(max_length=32, blank=True)
    ein = models.CharField(max_length=32, blank=True)
    address = models.CharField(max_length=255, blank=True)
    company_type = models.CharField(max_length=32, choices=CompanyType.choices)
    fleet_size = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner', 'name'], name='unique_owner_company_name')]
        indexes = [Index(fields=['owner']), Index(fields=['dot']), Index(fields=['mc'])]

    def __str__(self):
        return f"{self.name} ({self.owner})"
