from django.test import TestCase
from apps.faq.models import FaqCategory, FaqArticle


class FaqModelsTest(TestCase):
    def test_category_and_article_create(self):
        cat = FaqCategory.objects.create(name='Test Cat')
        art = FaqArticle.objects.create(category=cat, title='Test', content='Contenido')
        self.assertEqual(str(cat), 'Test Cat')
        self.assertEqual(str(art), 'Test')
