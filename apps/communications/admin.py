from django.contrib import admin
from .models import CommunicationChannel, CommunicationLog, CommSession, CommMessage, CommAttachment, CommSyncLog
from .models import WebhookEvent


@admin.register(CommunicationChannel)
class CommunicationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'channel', 'direction', 'status', 'timestamp')
    list_filter = ('channel', 'direction', 'status')
    search_fields = ('user__username', 'message')
    readonly_fields = ('timestamp',)


@admin.register(CommSession)
class CommSessionAdmin(admin.ModelAdmin):
    list_display = ('started_at', 'user', 'channel', 'direction', 'status', 'duration_sec', 'message_count', 'retell_call_id')
    list_filter = ('channel', 'direction', 'status', 'language')
    search_fields = ('user__username', 'retell_call_id', 'retell_conversation_id', 'intent', 'from_identity', 'to_identity')
    date_hierarchy = 'started_at'


@admin.register(CommMessage)
class CommMessageAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'session', 'role', 'channel', 'latency_ms', 'cost_usd')
    list_filter = ('role', 'channel')
    search_fields = ('content', 'provider_msg_id', 'session__retell_call_id')
    date_hierarchy = 'timestamp'


@admin.register(CommAttachment)
class CommAttachmentAdmin(admin.ModelAdmin):
    list_display = ('attach_type', 'mime_type', 'size_bytes', 'duration_sec', 'created_at')
    list_filter = ('attach_type',)
    search_fields = ('storage_path', 'mime_type')


@admin.register(CommSyncLog)
class CommSyncLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'ip', 'status_code', 'duration_ms')
    list_filter = ('status_code',)
    search_fields = ('user__username', 'ip')
    readonly_fields = ('created_at',)


"""Conversation model removed in favor of CommSession unified view."""


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('event_id', 'provider', 'created_at')
    list_filter = ('provider',)
    search_fields = ('event_id',)
    readonly_fields = ('created_at',)
