from django.contrib import admin
from .models import FaqCategory, FaqArticle, FaqAttachment


class FaqAttachmentInline(admin.TabularInline):
    model = FaqAttachment
    extra = 1


@admin.register(FaqCategory)
class FaqCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'ordering')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)
    list_filter = ('is_active',)


@admin.register(FaqArticle)
class FaqArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'is_featured', 'updated_at')
    search_fields = ('title', 'content')
    list_filter = ('category', 'is_published', 'is_featured')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [FaqAttachmentInline]
