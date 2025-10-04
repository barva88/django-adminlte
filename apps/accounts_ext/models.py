"""Extended account models for TRAUCK.

Defines a lightweight UserProfile that extends the AUTH_USER_MODEL via OneToOne.
"""
from django.conf import settings
from django.db import models
from django.db.models import Index
from apps.common.models import TimeStampedModel


# NOTE: This UserProfile is a shared place for lightweight user information.
# We keep the existing related_name 'truck_profile' for backward compatibility
# and expose a compatibility property `profile` on the user model where
# convenient (see property below).


class UserRole(models.TextChoices):
    CARRIER = "carrier", "Carrier"
    DRIVER = "driver", "Driver"
    DISPATCHER = "dispatcher", "Dispatcher"
    ADMIN = "admin", "Admin"


class UserProfile(TimeStampedModel):
    """Profile information tied 1:1 to a user.

    Extended with additional contact, address and company fields required by
    TRAUCK while preserving existing fields (phone, role, is_company_admin).
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='truck_profile'
    )

    # Existing/basic fields (preserved)
    phone = models.CharField(max_length=32, blank=True)
    role = models.CharField(max_length=32, choices=UserRole.choices, default=UserRole.CARRIER)
    is_company_admin = models.BooleanField(default=False)
    notes = models.TextField(blank=True)

    # New fields requested
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    # Address
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)

    # Company / regulatory numbers
    company_name = models.CharField(max_length=150, blank=True, null=True)
    dot_number = models.CharField(max_length=20, blank=True, null=True)
    mc_number = models.CharField(max_length=20, blank=True, null=True)

    # Preferences
    preferred_language = models.CharField(
        max_length=10,
        choices=[('en', 'English'), ('es', 'Español')],
        default='en'
    )
    timezone = models.CharField(max_length=50, default='UTC')

    class Meta:
        indexes = [Index(fields=['user'])]

    def __str__(self):
        return f"Profile: {getattr(self.user, 'username', str(self.pk))}"


    # Backwards-compatibility helper: provide `.profile` alias on the user
    # instance (accessed as `user.profile`) where some templates expect it.
    # We can't reliably monkeypatch the User model here, but we provide a
    # convenience property that views/templates can call via the reverse name
    # (user.truck_profile) or by using the `get_profile()` helper in code.

