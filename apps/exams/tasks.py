# tasks.py - Celery stubs; create real tasks if Celery is configured in the project
try:
    from celery import shared_task
except Exception:
    def shared_task(func=None, **kwargs):
        def wrapper(f):
            return f
        return wrapper


@shared_task
def sync_state_stats():
    # placeholder to aggregate stats periodically
    return True
