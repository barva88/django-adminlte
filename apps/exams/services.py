import random
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .models import Question, Choice, Exam, ExamAttempt, ExamAttemptAnswer, Subscription


EXAMS_QUESTIONS_PER_ATTEMPT = getattr(settings, 'EXAMS_QUESTIONS_PER_ATTEMPT', 20)


def select_questions_for_exam(exam: Exam):
    """Select a balanced set of questions for the exam.

    Strategy: attempt to pick according to distribution: 40% EASY, 40% MEDIUM, 20% HARD.
    If insufficient questions in a bucket, fill with other available active questions in the exam.category.
    Returns list of question IDs in random order of length EXAMS_QUESTIONS_PER_ATTEMPT.
    """
    per = EXAMS_QUESTIONS_PER_ATTEMPT

    # Determine targets
    target_easy = int(per * 0.4)
    target_medium = int(per * 0.4)
    target_hard = per - (target_easy + target_medium)

    qs_easy = list(Question.objects.filter(category=exam.category, difficulty='EASY', is_active=True).values_list('id', flat=True))
    qs_medium = list(Question.objects.filter(category=exam.category, difficulty='MEDIUM', is_active=True).values_list('id', flat=True))
    qs_hard = list(Question.objects.filter(category=exam.category, difficulty='HARD', is_active=True).values_list('id', flat=True))

    selected = []

    def take_from(bucket, n):
        take = bucket[:]
        random.shuffle(take)
        return take[:n]

    selected += take_from(qs_easy, target_easy)
    selected += take_from(qs_medium, target_medium)
    selected += take_from(qs_hard, target_hard)

    # If not enough, fill with other active questions in category
    if len(selected) < per:
        others = list(Question.objects.filter(category=exam.category, is_active=True).exclude(id__in=selected).values_list('id', flat=True))
        random.shuffle(others)
        needed = per - len(selected)
        selected += others[:needed]

    # If still not enough across category, get any active questions
    if len(selected) < per:
        others = list(Question.objects.filter(is_active=True).exclude(id__in=selected).values_list('id', flat=True))
        random.shuffle(others)
        needed = per - len(selected)
        selected += others[:needed]

    random.shuffle(selected)
    return selected[:per]


@transaction.atomic
def start_attempt(user, exam):
    # Validate subscription & credits
    sub = Subscription.objects.filter(user=user, status='active').first()
    if not sub or getattr(sub, 'credits_remaining', 0) <= 0:
        raise PermissionError('No active subscription or insufficient credits')

    # Prevent concurrent attempts
    in_progress = ExamAttempt.objects.filter(user=user, exam=exam, finished_at__isnull=True).exists()
    if in_progress:
        raise PermissionError('There is already an active attempt')

    q_ids = select_questions_for_exam(exam)
    attempt = ExamAttempt.objects.create(user=user, exam=exam, questions_snapshot={'questions': q_ids, 'order': q_ids})

    # Reduce credits
    sub.credits_remaining = getattr(sub, 'credits_remaining', 0) - 1
    sub.save()

    return attempt


@transaction.atomic
def finish_attempt(attempt: ExamAttempt, answers: dict):
    # answers: {question_id: choice_id}
    correct = 0
    total = len(attempt.questions_snapshot.get('questions', []))
    for qid in attempt.questions_snapshot.get('questions', []):
        choice_id = answers.get(str(qid)) or answers.get(qid)
        try:
            q = Question.objects.get(pk=qid)
        except Question.DoesNotExist:
            continue
        if choice_id:
            try:
                c = Choice.objects.get(pk=choice_id, question=q)
                is_correct = c.is_correct
            except Choice.DoesNotExist:
                is_correct = False
        else:
            is_correct = False
        ExamAttemptAnswer.objects.create(attempt=attempt, question=q, choice_id=choice_id or None, is_correct=is_correct)
        if is_correct:
            correct += 1

    score = (correct / total) * 100 if total > 0 else 0
    attempt.score = round(score, 2)
    attempt.passed = score >= 70.0
    attempt.finished_at = timezone.now()
    attempt.save()

    # Signals will update analytics; return attempt
    return attempt
