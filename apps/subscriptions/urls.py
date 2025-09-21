from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.index, name='index'),
    path('subscribe/', views.subscribe, name='subscribe'),
]
