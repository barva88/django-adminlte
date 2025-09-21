from django.apps import AppConfig


class ExamsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.exams'
    verbose_name = 'Exams (CDL)'

    def ready(self):
        # import signals to ensure they're registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
