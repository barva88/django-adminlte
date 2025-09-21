from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.db.models import Q
from django.urls import reverse
from .models import FaqCategory, FaqArticle
from .forms import FaqSearchForm
from rest_framework import viewsets, permissions
from .serializers import FaqCategorySerializer, FaqArticleSerializer


class FaqIndexView(View):
    def get(self, request):
        form = FaqSearchForm(request.GET or None)
        q = form.cleaned_data.get('q') if form.is_valid() else None
        categories = FaqCategory.objects.filter(is_active=True).order_by('ordering')
        articles = FaqArticle.objects.filter(is_published=True)
        if q:
            articles = articles.filter(Q(title__icontains=q) | Q(content__icontains=q))
        context = {'categories': categories, 'articles': articles[:10], 'form': form}
        return render(request, 'faq/faq_index.html', context)


class FaqCategoryView(View):
    def get(self, request, slug):
        category = get_object_or_404(FaqCategory, slug=slug, is_active=True)
        q = request.GET.get('q')
        articles = category.articles.filter(is_published=True)
        if q:
            articles = articles.filter(Q(title__icontains=q) | Q(content__icontains=q))
        context = {'category': category, 'articles': articles, 'q': q}
        return render(request, 'faq/faq_category.html', context)


class FaqDetailView(View):
    def post(self, request, slug):
        # feedback endpoint
        article = get_object_or_404(FaqArticle, slug=slug, is_published=True)
        helpful = request.POST.get('helpful')
        if helpful == 'true':
            article.helpful_votes = models.F('helpful_votes') + 1
        else:
            article.not_helpful_votes = models.F('not_helpful_votes') + 1
        article.save()
        return redirect(reverse('faq:article_detail', args=(slug,)))

    def get(self, request, slug):
        article = get_object_or_404(FaqArticle, slug=slug, is_published=True)
        # increment view count
        FaqArticle.objects.filter(pk=article.pk).update(view_count=models.F('view_count') + 1)
        article.refresh_from_db()
        context = {'article': article}
        return render(request, 'faq/faq_detail.html', context)


# DRF viewsets
class FaqCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FaqCategory.objects.filter(is_active=True).order_by('ordering')
    serializer_class = FaqCategorySerializer
    permission_classes = [permissions.AllowAny]


class FaqArticleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = FaqArticle.objects.filter(is_published=True).order_by('-is_featured', '-created_at')
    serializer_class = FaqArticleSerializer
    permission_classes = [permissions.AllowAny]
