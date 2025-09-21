from django.urls import path, include
from . import views
from rest_framework import routers

app_name = 'faq'

router = routers.DefaultRouter()
router.register(r'categories', views.FaqCategoryViewSet, basename='faqcategory')
router.register(r'articles', views.FaqArticleViewSet, basename='faqarticle')

urlpatterns = [
    path('', views.FaqIndexView.as_view(), name='index'),
    path('categoria/<slug:slug>/', views.FaqCategoryView.as_view(), name='category'),
    path('articulo/<slug:slug>/', views.FaqDetailView.as_view(), name='article_detail'),
    path('api/', include((router.urls, 'faq'), namespace='api')),
]
