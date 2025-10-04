from typing import Optional


def fetch_conversation_details(conversation_id: str, conv_type: str = 'call'):
    """
    Celery-friendly stub to fetch extra details for a conversation from Retell
    and update the Conversation record (e.g., transcript or recording_url).
    Replace with @shared_task if Celery is configured.
    """
    # Lazy import to avoid circulars
    from django.conf import settings
    from .models import CommSession, Channel
    import requests

    api_key = getattr(settings, 'RETELL_API_KEY', None)
    if not api_key:
        return

    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    try:
        if conv_type == 'call':
            url = getattr(settings, 'RETELL_GET_CALL_URL', 'https://api.retellai.com/get-call')
            r = requests.get(url, params={'call_id': conversation_id}, headers=headers, timeout=15)
            if r.ok:
                data = r.json() or {}
                rec = data.get('recording_url') or data.get('recordingUrl')
                if rec:
                    CommSession.objects.filter(retell_call_id=conversation_id).update(metadata={"recording_url": rec})
        else:
            url = getattr(settings, 'RETELL_GET_CONVERSATION_URL', 'https://api.retellai.com/get-conversation')
            r = requests.get(url, params={'conversation_id': conversation_id}, headers=headers, timeout=15)
            if r.ok:
                data = r.json() or {}
                tr = data.get('transcript') or (data.get('summary') or {}).get('overall')
                if tr:
                    # Store transcript excerpt only (full messages handled elsewhere)
                    CommSession.objects.filter(retell_conversation_id=conversation_id).update(transcript_excerpt=tr[:180])
    except Exception:
        # Swallow errors silently for now
        return
