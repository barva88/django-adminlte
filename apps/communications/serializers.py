from rest_framework import serializers
from .models import CommunicationChannel, CommunicationLog, ConversationMemory


class CommunicationChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunicationChannel
        fields = ('id', 'name', 'description', 'is_active')


class CommunicationLogSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    channel = serializers.PrimaryKeyRelatedField(queryset=CommunicationChannel.objects.filter(is_active=True))

    class Meta:
        model = CommunicationLog
        fields = ('id', 'user', 'channel', 'direction', 'message', 'timestamp', 'status')
        read_only_fields = ('timestamp', 'status')


class ConversationMemorySerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = ConversationMemory
        fields = ('id', 'user', 'session_id', 'messages', 'last_updated')
        read_only_fields = ('id', 'session_id', 'last_updated', 'user')
