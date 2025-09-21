from rest_framework import serializers
from .models import SupportTopic, SupportTicket


class SupportTopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTopic
        fields = ('id', 'name', 'slug')


class SupportTicketSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ('id', 'user', 'email', 'topic', 'subject', 'message', 'status', 'priority', 'created_at', 'updated_at')
        read_only_fields = ('user', 'created_at', 'updated_at')
