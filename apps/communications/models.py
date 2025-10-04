from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


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


# --- Extended Communications Schema (sessions/messages/attachments) ---

class Channel(models.TextChoices):
    WHATSAPP = "whatsapp", "WhatsApp"
    VOICE    = "voice", "Voz (Retell)"
    WEB      = "web", "Web/Chat"


class Direction(models.TextChoices):
    INBOUND  = "inbound", "Entrante"
    OUTBOUND = "outbound", "Saliente"


class CommStatus(models.TextChoices):
    COMPLETED = "completed", "Completada"
    FAILED    = "failed", "Fallida"
    MISSED    = "missed", "Perdida/No contestada"
    CANCELED  = "canceled", "Cancelada"
    ONGOING   = "ongoing", "En curso"


class MessageRole(models.TextChoices):
    USER      = "user", "Usuario"
    ASSISTANT = "assistant", "Asistente (IA)"
    AGENT     = "agent", "Agente Humano"
    SYSTEM    = "system", "Sistema"


class CommSession(models.Model):
    """
    Registro principal de una comunicación con Retell/Twilio/WhatsApp/Web.
    Ideal para la lista del módulo: canal, estado, duración, conteo de mensajes, costos y resumen.
    """
    tenant = models.UUIDField(default=uuid.uuid4, db_index=True)  # default UUID para evitar migración bloqueante
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="comm_sessions",
    )

    # Identificadores de proveedores (útiles para reconciliar y deduplicar)
    retell_conversation_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    retell_call_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    twilio_call_sid = models.CharField(max_length=64, null=True, blank=True, db_index=True)
    whatsapp_msg_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)
    external_ref = models.CharField(max_length=128, null=True, blank=True, help_text="ID externo adicional (si aplica)")

    # Atributos operativos
    channel = models.CharField(max_length=16, choices=Channel.choices)
    direction = models.CharField(max_length=16, choices=Direction.choices)
    status = models.CharField(max_length=16, choices=CommStatus.choices, default=CommStatus.ONGOING)
    # Proveedor (retell, twilio, whatsapp, web, etc.)
    provider = models.CharField(max_length=32, default="retell", db_index=True)
    # ID de flujo conversacional (cuando aplique)
    conversation_flow_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)

    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_sec = models.PositiveIntegerField(default=0)

    message_count = models.PositiveIntegerField(default=0)
    language = models.CharField(max_length=12, default="es", help_text="código ISO (es, en, etc.)")
    intent = models.CharField(max_length=64, null=True, blank=True, help_text="intención/dominio detectado")
    resolved = models.BooleanField(default=False)

    # Contrapartes (útil para voz/WhatsApp)
    from_identity = models.CharField(max_length=128, null=True, blank=True, help_text="quién inicia (tel/JID)")
    to_identity = models.CharField(max_length=128, null=True, blank=True, help_text="destino (tel/JID)")

    # Costeo y consumo (para panel y alertas)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    tokens_prompt = models.PositiveIntegerField(default=0)
    tokens_completion = models.PositiveIntegerField(default=0)
    voice_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transcription_minutes = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Resumen/extracto para listar sin abrir detalles
    transcript_excerpt = models.TextField(null=True, blank=True)

    # Técnica/diagnóstico
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    # Payload bruto del proveedor para auditoría y sincronización incremental
    provider_payload = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "started_at"]),
            models.Index(fields=["tenant", "channel", "started_at"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "user", "started_at"]),
        ]
        ordering = ("-started_at",)

    def __str__(self):
        return f"[{self.get_channel_display()}] {self.started_at:%Y-%m-%d %H:%M} · {self.get_status_display()}"

    def close(self, ended_at=None):
        """Helper para cerrar sesión y calcular duración."""
        self.ended_at = ended_at or timezone.now()
        self.duration_sec = max(0, int((self.ended_at - self.started_at).total_seconds()))
        if not self.status:
            self.status = CommStatus.COMPLETED
        self.save(update_fields=["ended_at", "duration_sec", "status", "updated_at"])


class CommMessage(models.Model):
    """
    Mensajes atómicos dentro de una CommSession (para auditoría y análisis).
    """
    session = models.ForeignKey(CommSession, on_delete=models.CASCADE, related_name="messages")
    tenant = models.UUIDField(default=uuid.uuid4, db_index=True)

    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    channel = models.CharField(max_length=16, choices=Channel.choices)
    role = models.CharField(max_length=16, choices=MessageRole.choices)
    content = models.TextField(null=True, blank=True)
    provider_msg_id = models.CharField(max_length=128, null=True, blank=True, db_index=True)

    # Métricas por mensaje (opcional pero útil)
    latency_ms = models.PositiveIntegerField(default=0)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    cost_usd = models.DecimalField(max_digits=10, decimal_places=5, default=0)

    has_attachments = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "timestamp"]),
            models.Index(fields=["tenant", "session", "timestamp"]),
            models.Index(fields=["tenant", "role"]),
        ]
        ordering = ("timestamp",)

    def __str__(self):
        return f"{self.timestamp:%H:%M:%S} · {self.get_role_display()}"


class CommAttachment(models.Model):
    """
    Adjuntos asociados a un mensaje (audio de llamada, grabación, documento, imagen, etc.).
    """
    AUDIO = "audio"
    IMAGE = "image"
    DOC = "document"
    OTHER = "other"
    ATTACH_TYPES = (
        (AUDIO, "Audio"),
        (IMAGE, "Imagen"),
        (DOC, "Documento"),
        (OTHER, "Otro"),
    )

    message = models.ForeignKey(CommMessage, on_delete=models.CASCADE, related_name="attachments")
    tenant = models.UUIDField(default=uuid.uuid4, db_index=True)

    attach_type = models.CharField(max_length=16, choices=ATTACH_TYPES, default=AUDIO)
    storage_path = models.CharField(max_length=512, help_text="ruta/URL al archivo (S3, etc.)")
    mime_type = models.CharField(max_length=64, null=True, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    duration_sec = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["tenant", "attach_type"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self):
        return f"{self.attach_type} · {self.mime_type or ''} ({self.size_bytes}B)"


class CommSyncLog(models.Model):
    """Temporal log for Retell sync attempts to aid diagnostics."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    status_code = models.PositiveIntegerField(default=0)
    duration_ms = models.PositiveIntegerField(default=0)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Sync {self.created_at:%Y-%m-%d %H:%M:%S} · {self.status_code}"


"""Conversation model removed (merged into CommSession)."""


class WebhookEvent(models.Model):
    """Idempotency store for webhook events."""
    event_id = models.CharField(max_length=128, unique=True, db_index=True)
    provider = models.CharField(max_length=32, default='retell', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider}:{self.event_id}"

class ConversationMemory(models.Model):
    """Per-user conversation memory for Retell context."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversation_memories')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    messages = models.JSONField(default=list, blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def append_message(self, role: str, content: str, meta: dict = None):
        lst = list(self.messages or [])
        item = {
            'role': (role or '').lower(),
            'content': content or '',
            'ts': timezone.now().isoformat(),
        }
        if meta:
            item['meta'] = meta
        lst.append(item)
        self.messages = lst
        self.save(update_fields=['messages', 'last_updated'])

    def __str__(self):
        return f"ConversationMemory(user={self.user_id}, session={self.session_id})"

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['last_updated']),
        ]
