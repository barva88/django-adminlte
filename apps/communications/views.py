from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CommunicationChannel, CommunicationLog
from .serializers import CommunicationChannelSerializer, CommunicationLogSerializer


class CommunicationChannelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommunicationChannel.objects.filter(is_active=True).order_by('name')
    serializer_class = CommunicationChannelSerializer
    permission_classes = [permissions.IsAuthenticated]


class CommunicationLogViewSet(viewsets.ModelViewSet):
    queryset = CommunicationLog.objects.all()
    serializer_class = CommunicationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # users can only see their own logs unless superuser
        user = self.request.user
        if user.is_superuser:
            return CommunicationLog.objects.all()
        return CommunicationLog.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
