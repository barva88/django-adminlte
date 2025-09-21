from django.urls import path
from . import views

app_name = 'exams'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('history/', views.history, name='history'),
    path('list/', views.exam_list, name='exam_list'),
    path('take/<int:exam_id>/', views.exam_take, name='exam_take'),
    path('detail/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('result/<int:attempt_id>/', views.exam_result, name='exam_result'),
    path('stats/', views.stats, name='stats'),
    path('bank/', views.bank, name='bank'),

    # API endpoints
    path('api/analytics/users_by_state/', views.api_users_by_state, name='api_users_by_state'),
    path('api/analytics/monthly_revenue/', views.api_monthly_revenue, name='api_monthly_revenue'),
    path('api/analytics/attempts_summary/', views.api_attempts_summary, name='api_attempts_summary'),
]
