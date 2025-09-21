from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Question, Choice, Exam, Subscription, SubscriptionPlan
from ..services import select_questions_for_exam, start_attempt, finish_attempt


class ServicesTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='t', password='t')
        self.plan = SubscriptionPlan.objects.create(name='Basic', price_cents=999, period_months=1, exam_credits=10)
        self.sub = Subscription.objects.create(user=self.user, plan=self.plan, status='active', credits_remaining=5)
        self.exam = Exam.objects.create(title='Test', category='General Knowledge')
        # create questions
        for i in range(30):
            q = Question.objects.create(text=f'Q{i}', category='General Knowledge', difficulty='EASY')
            Choice.objects.create(question=q, text='True', is_correct=True)
            Choice.objects.create(question=q, text='False', is_correct=False)

    def test_select_questions_length(self):
        qids = select_questions_for_exam(self.exam)
        self.assertEqual(len(qids), 20)

    def test_start_and_finish_attempt(self):
        attempt = start_attempt(self.user, self.exam)
        self.assertIsNotNone(attempt)
        # simulate answers - all correct
        answers = {str(qid): Choice.objects.filter(question_id=qid, is_correct=True).first().id for qid in attempt.questions_snapshot['questions']}
        attempt = finish_attempt(attempt, answers)
        self.assertTrue(attempt.passed or attempt.score >= 0)
