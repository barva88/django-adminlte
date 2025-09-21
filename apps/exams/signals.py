from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Subscription


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def give_initial_credits(sender, instance, created, **kwargs):
    """Give newly registered users a free 10 exam credits by creating or updating
    an Exam Subscription record. This is idempotent and safe to call multiple
    times.

    Behavior:
    - If a Subscription for the user exists, ensure `credits_remaining` is at
      least 10 (do not reduce existing credits).
    - If none exist, create an active Subscription with 10 credits and no plan.
    """
    if not created:
        return

    try:
        sub, _ = Subscription.objects.get_or_create(user=instance, defaults={
            'status': 'active',
            'credits_remaining': 10,
        })
        # If subscription existed but had fewer than 10 credits, top up to 10
        if sub.credits_remaining < 10:
            sub.credits_remaining = 10
            sub.save(update_fields=['credits_remaining'])
    except Exception:
        # Fail silently to avoid blocking user creation (logging optional)
        pass
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ExamAttempt, StateStat
from django.utils import timezone


@receiver(post_save, sender=ExamAttempt)
def update_state_stats_on_attempt_save(sender, instance: ExamAttempt, created, **kwargs):
    # Only process when finished_at is set (attempt completed)
    if instance.finished_at:
        month = instance.finished_at.strftime('%Y-%m')
        # best-effort inference of user state from common profile shapes
        state = None
        profile = getattr(instance.user, 'profile', None)
        if profile:
            # common attribute names
            for attr in ('state', 'state_code', 'region', 'province'):
                val = getattr(profile, attr, None)
                if val:
                    state = val
                    break
            # try nested address
            if not state:
                addr = getattr(profile, 'address', None)
                if addr:
                    state = getattr(addr, 'state', None) or getattr(addr, 'region', None)

        if not state:
            # fallback to default 'US'
            state = 'US'

        stat, _ = StateStat.objects.get_or_create(state_code=state, month=month)
        stat.attempts_count = (stat.attempts_count or 0) + 1
        # maintain a pass_count field on the instance via attr (not schema change) for aggregation convenience
        passed_count = getattr(stat, 'passed_count', 0)
        if instance.passed:
            from django.db.models.signals import post_save
            from django.dispatch import receiver
            from .models import ExamAttempt, StateStat
            from django.utils import timezone


            @receiver(post_save, sender=ExamAttempt)
            def update_state_stats_on_attempt_save(sender, instance: ExamAttempt, created, **kwargs):
                # Only process when finished_at is set (attempt completed)
                if instance.finished_at:
                    month = instance.finished_at.strftime('%Y-%m')
                    # best-effort inference of user state from common profile shapes
                    state = None
                    profile = getattr(instance.user, 'profile', None)
                    if profile:
                        # common attribute names
                        for attr in ('state', 'state_code', 'region', 'province'):
                            val = getattr(profile, attr, None)
                            if val:
                                state = val
                                break
                        # try nested address
                        if not state:
                            addr = getattr(profile, 'address', None)
                            if addr:
                                state = getattr(addr, 'state', None) or getattr(addr, 'region', None)

                    if not state:
                        # fallback to default 'US'
                        state = 'US'

                    stat, _ = StateStat.objects.get_or_create(state_code=state, month=month)
                    stat.attempts_count = (stat.attempts_count or 0) + 1
                    # maintain a pass_count field on the instance via attr (not schema change) for aggregation convenience
                    passed_count = getattr(stat, 'passed_count', 0)
                    if instance.passed:
                        passed_count += 1
                    # recompute pass_rate
                    total = stat.attempts_count
                    stat.pass_rate = (passed_count / total) * 100 if total > 0 else 0
                    # save the helper value in a non-persistent attribute is fine, but prefer storing in model in future
                    stat.save()
