"""Extended account models for TRAUCK.

Defines a lightweight UserProfile that extends the AUTH_USER_MODEL via OneToOne.
"""
from django.conf import settings
from django.db import models
from django.db.models import Index
from apps.common.models import TimeStampedModel


class UserRole(models.TextChoices):
    CARRIER = "carrier", "Carrier"
    DRIVER = "driver", "Driver"
    DISPATCHER = "dispatcher", "Dispatcher"
    ADMIN = "admin", "Admin"


class UserProfile(TimeStampedModel):
    """Profile information tied 1:1 to a user.

    Stores phone, role and lightweight flags for future use.
    """

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='truck_profile')
    phone = models.CharField(max_length=32, blank=True)
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.CARRIER)
    is_company_admin = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [Index(fields=['user'])]

    def __str__(self):
        return f"Profile: {getattr(self.user, 'username', str(self.pk))}"
