from rest_framework import serializers
from .models import FaqCategory, FaqArticle, FaqAttachment


class FaqAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqAttachment
        fields = ('id', 'file', 'description')


class FaqCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqCategory
        fields = ('id', 'name', 'slug', 'description')


class FaqArticleSerializer(serializers.ModelSerializer):
    attachments = FaqAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = FaqArticle
        fields = ('id', 'category', 'title', 'slug', 'content', 'is_published', 'is_featured', 'view_count', 'helpful_votes', 'not_helpful_votes', 'created_at', 'updated_at', 'attachments')
