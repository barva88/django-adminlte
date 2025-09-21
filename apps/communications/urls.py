from rest_framework import routers
from django.urls import path, include
from .views import CommunicationChannelViewSet, CommunicationLogViewSet

router = routers.DefaultRouter()
router.register(r'channels', CommunicationChannelViewSet, basename='communicationchannel')
router.register(r'logs', CommunicationLogViewSet, basename='communicationlog')

urlpatterns = [
    path('', include(router.urls)),
]
