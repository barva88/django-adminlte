from rest_framework import serializers
from .models import Question, Choice, Exam, ExamAttempt, ExamAttemptAnswer


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ('id', 'text', 'is_correct')


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True)

    class Meta:
        model = Question
        fields = ('id', 'text', 'image', 'difficulty', 'category', 'choices')


class ExamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Exam
        fields = ('id', 'title', 'category')


class ExamAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamAttempt
        fields = ('id', 'user', 'exam', 'questions_snapshot', 'score', 'passed', 'started_at', 'finished_at')
