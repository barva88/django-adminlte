from django.contrib import admin
from .models import Question, Choice, Exam, SubscriptionPlan, Subscription, ExamAttempt, ExamAttemptAnswer


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'difficulty', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('text',)
    inlines = [ChoiceInline]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('title',)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_cents', 'exam_credits')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'credits_remaining')


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'exam', 'score', 'passed', 'started_at', 'finished_at')
    list_filter = ('exam', 'passed')


@admin.register(ExamAttemptAnswer)
class ExamAttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'choice', 'is_correct')
