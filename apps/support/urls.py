from django.urls import path, include
from . import views
from rest_framework import routers

app_name = 'support'

router = routers.DefaultRouter()
router.register(r'topics', views.SupportTopicViewSet, basename='supporttopic')
router.register(r'tickets', views.SupportTicketViewSet, basename='supportticket')

urlpatterns = [
    path('', views.SupportIndexView.as_view(), name='index'),
    path('nuevo/', views.SupportNewView.as_view(), name='new_ticket'),
    path('mis-tickets/', views.SupportMyTicketsView.as_view(), name='my_tickets'),
    path('ticket/<int:id>/', views.SupportTicketDetailView.as_view(), name='ticket_detail'),
    path('api/', include((router.urls, 'support'), namespace='api')),
]
