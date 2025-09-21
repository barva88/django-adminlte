from .models import Exam, Question


def get_active_exams(q=None):
    qs = Exam.objects.filter(is_active=True)
    if q:
        qs = qs.filter(title__icontains=q)
    return qs
