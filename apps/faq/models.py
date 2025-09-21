from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class FaqCategory(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('ordering', 'name')
        verbose_name = _('FAQ Category')
        verbose_name_plural = _('FAQ Categories')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FaqArticle(models.Model):
    category = models.ForeignKey(FaqCategory, on_delete=models.PROTECT, related_name='articles')
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    helpful_votes = models.PositiveIntegerField(default=0)
    not_helpful_votes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-is_featured', '-created_at')
        indexes = [models.Index(fields=['category', 'is_published'])]
        verbose_name = _('FAQ Article')
        verbose_name_plural = _('FAQ Articles')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class FaqAttachment(models.Model):
    article = models.ForeignKey(FaqArticle, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='faq/')
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.description or str(self.file)
