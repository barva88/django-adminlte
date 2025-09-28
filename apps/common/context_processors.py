from django.conf import settings


def retell_settings(request):
    """Expose Retell embed-related settings to templates.

    Note: public widget key is intentionally separate from the server-side
    RETELL_API_KEY so secrets remain on the backend.
    """
    return {
        'RETELL_EMBED_URL': getattr(settings, 'RETELL_EMBED_URL', ''),
        'RETELL_EMBED_ENABLED': getattr(settings, 'RETELL_EMBED_ENABLED', False),
        'RETELL_EMBED_OPEN_FN': getattr(settings, 'RETELL_EMBED_OPEN_FN', ''),
        'RETELL_PUBLIC_KEY': getattr(settings, 'RETELL_PUBLIC_KEY', ''),
    'RETELL_DISABLE_RECAPTCHA': getattr(settings, 'RETELL_DISABLE_RECAPTCHA', False),
        'PHONE_NUMBER': getattr(settings, 'PHONE_NUMBER', ''),
    }
