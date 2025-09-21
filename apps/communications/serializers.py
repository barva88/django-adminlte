from rest_framework import serializers
from .models import CommunicationChannel, CommunicationLog


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
