from django.db import models
from django.conf import settings
from django.utils import timezone


class Question(models.Model):
    DIFFICULTY_CHOICES = (
        ('EASY', 'Easy'),
        ('MEDIUM', 'Medium'),
        ('HARD', 'Hard'),
    )

    text = models.TextField()
    image = models.ImageField(upload_to='exams/questions/', null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='EASY', db_index=True)
    category = models.CharField(max_length=100, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=['category', 'difficulty', 'is_active']),
        ]

    def __str__(self):
        return f"{self.category}: {self.text[:60]}"


class Choice(models.Model):
    question = models.ForeignKey(Question, related_name='choices', on_delete=models.CASCADE)
    text = models.CharField(max_length=400)
    is_correct = models.BooleanField(default=False)

    class Meta:
        unique_together = (('question', 'is_correct'),)

    def __str__(self):
        return self.text


class Exam(models.Model):
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ExamAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    questions_snapshot = models.JSONField()
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)
    started_at = models.DateTimeField(default=timezone.now)
    finished_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        indexes = [models.Index(fields=['user', 'finished_at'])]

    def __str__(self):
        return f"Attempt {self.pk} - {self.user} - {self.exam}"


class ExamAttemptAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, related_name='answers', on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Answer {self.pk} - Attempt {self.attempt_id}"


# Subscriptions/payments stubs (idempotent if a separate payments app exists)
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price_cents = models.IntegerField(default=0)
    period_months = models.IntegerField(default=1)
    exam_credits = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Subscription(models.Model):
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    credits_remaining = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user} - {self.plan} ({self.status})"


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    amount_cents = models.IntegerField(default=0)
    status = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class StateStat(models.Model):
    state_code = models.CharField(max_length=2)
    month = models.CharField(max_length=7)  # YYYY-MM
    users_count = models.IntegerField(default=0)
    attempts_count = models.IntegerField(default=0)
    pass_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    class Meta:
        unique_together = (('state_code', 'month'),)

    def __str__(self):
        return f"{self.state_code} - {self.month}"
