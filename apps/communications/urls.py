from rest_framework import routers
from django.urls import path, include
from .views import (
    CommunicationChannelViewSet,
    CommunicationLogViewSet,
    RetellProxyView,
    RetellCreateWebCallView,
    CommSessionListView,
    RetellSyncWebhookView,
    latest_sync_log,
    RetellListConversationFlowsView,
    RetellListConversationsView,
    RetellListCallsView,
    RetellSyncNowView,
    CommSessionDetailApiView,
    ConversationMemoryViewSet,
    RetellSimulateConversationView,
    RetellWebhookView,
    MyConversationsListView,
    CommSessionTablePartialView,
)

router = routers.DefaultRouter()
router.register(r'channels', CommunicationChannelViewSet, basename='communicationchannel')
router.register(r'logs', CommunicationLogViewSet, basename='communicationlog')
router.register(r'memory', ConversationMemoryViewSet, basename='conversationmemory')

urlpatterns = [
    path('', include(router.urls)),
    path('retell/', RetellProxyView.as_view(), name='retell_proxy'),
    path('retell/create-web-call/', RetellCreateWebCallView.as_view(), name='retell_create_web_call'),
    path('retell/list-conversation-flows/', RetellListConversationFlowsView.as_view(), name='retell_list_conversation_flows'),
    path('retell/list-conversations/', RetellListConversationsView.as_view(), name='retell_list_conversations'),
    path('retell/list-calls/', RetellListCallsView.as_view(), name='retell_list_calls'),
    path('retell/sync/<str:token>/', RetellSyncWebhookView.as_view(), name='retell_sync'),
    path('retell/sync-latest-log/', latest_sync_log, name='retell_sync_latest_log'),
    path('retell/sync-now/', RetellSyncNowView.as_view(), name='retell_sync_now'),
    path('retell/simulate-conversation/', RetellSimulateConversationView.as_view(), name='retell_simulate_conversation'),
    path('retell/webhook/', RetellWebhookView.as_view(), name='retell_webhook'),
    path('my/conversations/', MyConversationsListView.as_view(), name='my_conversations'),
    path('sessions/', CommSessionListView.as_view(), name='comm_session_list'),
    path('sessions/partial/table/', CommSessionTablePartialView.as_view(), name='comm_session_table_partial'),
    path('sessions/<int:pk>/detail/', CommSessionDetailApiView.as_view(), name='comm_session_detail_api'),
]
