from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import SubscriptionPlan, Subscription, Exam, Question, Choice
from ..services import start_attempt


class RulesTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='rules', password='pass')
        plan = SubscriptionPlan.objects.create(name='Basic', price_cents=999, period_months=1, exam_credits=10)
        self.sub = Subscription.objects.create(user=self.user, plan=plan, status='active', credits_remaining=2)
        self.exam = Exam.objects.create(title='Test', category='General Knowledge')
        # create 20 questions
        for i in range(20):
            q = Question.objects.create(text=f'Q{i}', category='General Knowledge', difficulty='EASY')
            Choice.objects.create(question=q, text='True', is_correct=True)
            Choice.objects.create(question=q, text='False', is_correct=False)

    def test_credits_decrement(self):
        attempt = start_attempt(self.user, self.exam)
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.credits_remaining, 1)

    def test_prevent_concurrent(self):
        a1 = start_attempt(self.user, self.exam)
        try:
            a2 = start_attempt(self.user, self.exam)
            self.fail('Expected PermissionError for concurrent attempt')
        except PermissionError:
            pass
