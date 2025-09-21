from django.db import models
from django.conf import settings


class CommunicationChannel(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Communication Channel'
        verbose_name_plural = 'Communication Channels'

    def __str__(self):
        return self.name


class CommunicationLog(models.Model):
    DIRECTION_INCOMING = 'incoming'
    DIRECTION_OUTGOING = 'outgoing'
    DIRECTION_CHOICES = (
        (DIRECTION_INCOMING, 'Incoming'),
        (DIRECTION_OUTGOING, 'Outgoing'),
    )

    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_RECEIVED = 'received'
    STATUS_FAILED = 'failed'
    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_SENT, 'Sent'),
        (STATUS_RECEIVED, 'Received'),
        (STATUS_FAILED, 'Failed'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='communications')
    channel = models.ForeignKey(CommunicationChannel, on_delete=models.PROTECT, related_name='logs')
    direction = models.CharField(max_length=12, choices=DIRECTION_CHOICES)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Communication Log'
        verbose_name_plural = 'Communication Logs'

    def __str__(self):
        return f"{self.user} - {self.channel} - {self.direction} @ {self.timestamp:%Y-%m-%d %H:%M}"
