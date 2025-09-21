from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from .models import Exam, Question, ExamAttempt
from .services import start_attempt, finish_attempt
from django.core.paginator import Paginator
from django.conf import settings


@login_required
def dashboard(request):
    # Minimal user dashboard: attempts, credits
    attempts = ExamAttempt.objects.filter(user=request.user).order_by('-started_at')[:10]
    # credits
    credits = 0
    try:
        from .models import Subscription
        sub = Subscription.objects.filter(user=request.user, status='active').first()
        if sub:
            credits = sub.credits_remaining
    except Exception:
        credits = 0
    return render(request, 'exams/dashboard.html', {'attempts': attempts, 'credits': credits})


@login_required
def exam_list(request):
    q = request.GET.get('q', '')
    exams = Exam.objects.filter(is_active=True)
    if q:
        exams = exams.filter(title__icontains=q)
    paginator = Paginator(exams, 20)
    page = request.GET.get('page')
    exams_page = paginator.get_page(page)
    # Build a map of in-progress attempt ids for the current user per exam
    exam_ids = [e.id for e in exams_page.object_list]
    attempts = ExamAttempt.objects.filter(user=request.user, exam_id__in=exam_ids, finished_at__isnull=True)
    attempt_map = {a.exam_id: a.id for a in attempts}
    # Also fetch last finished attempt score per exam (if any)
    finished = ExamAttempt.objects.filter(user=request.user, exam_id__in=exam_ids, finished_at__isnull=False).order_by('exam_id', '-finished_at')
    score_map = {}
    # keep first (latest) finished per exam
    seen = set()
    for a in finished:
        if a.exam_id in seen:
            continue
        seen.add(a.exam_id)
        score_map[a.exam_id] = a.score
    return render(request, 'exams/exam_list.html', {'exams': exams_page, 'q': q, 'attempt_map': attempt_map, 'score_map': score_map})


@login_required
def exam_take(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id, is_active=True)
    # Start attempt if POST start
    if request.method == 'POST' and request.POST.get('action') == 'start':
        try:
            attempt = start_attempt(request.user, exam)
            return redirect('exams:exam_take', exam_id=exam.id)
        except PermissionError as e:
            return HttpResponseForbidden(str(e))

    # Find in-progress attempt
    attempt = ExamAttempt.objects.filter(user=request.user, exam=exam, finished_at__isnull=True).first()
    if attempt:
        questions_ids = attempt.questions_snapshot.get('questions', [])
    else:
        # present start button
        questions_ids = []
    # Fetch questions (preserve order)
    questions = []
    if questions_ids:
        qs = Question.objects.filter(id__in=questions_ids).prefetch_related('choices')
        # reorder to original
        id_map = {q.id: q for q in qs}
        questions = [id_map[qid] for qid in questions_ids if qid in id_map]

    return render(request, 'exams/exam_take.html', {'exam': exam, 'questions': questions, 'attempt': attempt})


@login_required
def exam_result(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, pk=attempt_id, user=request.user)
    return render(request, 'exams/exam_result.html', {'attempt': attempt})


@login_required
def history(request):
    # blank history page placeholder
    return render(request, 'exams/history.html', {})


@login_required
def stats(request):
    # blank statistics page placeholder
    return render(request, 'exams/stats.html', {})


@login_required
def bank(request):
    # blank exam bank / catalogs placeholder
    return render(request, 'exams/bank.html', {})


@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, pk=exam_id)
    return render(request, 'exams/exam_detail.html', {'exam': exam})


# API endpoints
@login_required
def api_users_by_state(request):
    # return simple aggregated structure
    from .models import StateStat
    stats = StateStat.objects.all()
    out = {}
    for s in stats:
        out.setdefault(s.state_code, {})[s.month] = {
            'users': s.users_count,
            'attempts': s.attempts_count,
            'pass_rate': float(s.pass_rate or 0)
        }
    return JsonResponse(out)


@login_required
def api_monthly_revenue(request):
    from .models import Payment
    # aggregate by month
    payments = Payment.objects.all()
    out = {}
    for p in payments:
        m = p.created_at.strftime('%Y-%m')
        out.setdefault(m, 0)
        out[m] += p.amount_cents or 0
    # return usd
    series = [{'month': k, 'amount_cents': v} for k, v in sorted(out.items())]
    return JsonResponse({'series': series})


@login_required
def api_attempts_summary(request):
    from .models import ExamAttempt
    from django.db.models import Count, Avg
    qs = ExamAttempt.objects.all()
    by_month = qs.extra({'month': "strftime('%%Y-%%m', finished_at)"}).values('month').annotate(total=Count('id'), avg_score=Avg('score'))
    data = [{'month': r['month'], 'total': r['total'], 'avg_score': float(r['avg_score'] or 0)} for r in by_month]
    return JsonResponse({'months': data})
