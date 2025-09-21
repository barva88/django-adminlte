from django.contrib import admin
from .models import SupportTopic, SupportTicket


@admin.register(SupportTopic)
class SupportTopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'ordering')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'email', 'status', 'priority', 'updated_at')
    list_filter = ('status', 'priority', 'topic')
    search_fields = ('subject', 'message', 'email')
    actions = ['mark_closed']

    def mark_closed(self, request, queryset):
        queryset.update(status=SupportTicket.STATUS_CLOSED)
    mark_closed.short_description = 'Marcar seleccionados como cerrados'
