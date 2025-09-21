from django.contrib import admin
from .models import CommunicationChannel, CommunicationLog


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
