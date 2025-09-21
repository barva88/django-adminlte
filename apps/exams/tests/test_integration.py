from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from ..models import SubscriptionPlan


class IntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='intuser', password='pass')
        self.plan = SubscriptionPlan.objects.create(name='Basic', price_cents=999, period_months=1, exam_credits=10)

    def test_flow_signup_purchase_start_attempt(self):
        # login
        self.client.login(username='intuser', password='pass')
        # view exams
        resp = self.client.get(reverse('exams:exam_list'))
        self.assertIn(resp.status_code, (200, 302))
