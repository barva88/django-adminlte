from django.apps import AppConfig


class AccountsExtConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts_ext'
    verbose_name = 'Accounts Extensions (TRAUCK)'

    def ready(self):
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
