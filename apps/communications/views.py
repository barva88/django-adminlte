from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CommunicationChannel, CommunicationLog, CommSession, Channel, Direction, CommStatus, ConversationMemory
from .serializers import CommunicationChannelSerializer, CommunicationLogSerializer, ConversationMemorySerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.conf import settings
import requests
from datetime import datetime, timezone as dt_timezone, timedelta
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.db.models import Q
from django.views import View
from django.http import JsonResponse, HttpResponseForbidden, HttpResponseRedirect
import time
from rest_framework.test import APIRequestFactory
from django.views.decorators.http import require_GET
import hmac
import hashlib
import json as jsonlib


class CommunicationChannelViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommunicationChannel.objects.filter(is_active=True).order_by('name')
    serializer_class = CommunicationChannelSerializer
    permission_classes = [permissions.IsAuthenticated]


class CommunicationLogViewSet(viewsets.ModelViewSet):
    queryset = CommunicationLog.objects.all()
    serializer_class = CommunicationLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # users can only see their own logs unless superuser
        user = self.request.user
        if user.is_superuser:
            return CommunicationLog.objects.all()
        return CommunicationLog.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class RetellProxyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # expects JSON {"message": "..."}
        msg = (request.data.get('message') or '').strip()
        if not msg:
            return Response({'error': 'empty message'}, status=400)

        api_url = getattr(settings, 'RETELL_API_URL', None)
        api_key = getattr(settings, 'RETELL_API_KEY', None)
        api_model = getattr(settings, 'RETELL_API_MODEL', None)
        api_agent = getattr(settings, 'RETELL_AGENT_ID', None)

        # debug info (safe to remove in production)
        print('[RetellProxyView] settings ->', {
            'RETELL_MOCK': getattr(settings, 'RETELL_MOCK', None),
            'RETELL_API_URL_set': bool(api_url),
            'RETELL_API_KEY_set': bool(api_key),
            'RETELL_API_MODEL': api_model,
            'RETELL_AGENT_ID': api_agent,
        })

        # allow overriding model/agent per-request from the frontend
        req_agent = request.data.get('agent_id') or request.data.get('agent')
        req_model = request.data.get('model')
        if req_agent:
            api_agent = req_agent
        if req_model:
            api_model = req_model

        # If RETELL_MOCK is enabled, always return the canned response for local UI work
        if getattr(settings, 'RETELL_MOCK', False):
            mock = {
                'message': 'Respuesta de prueba: recibí su mensaje',
                'success': True,
                'provider_text': f"Echo: {msg}"
            }
            return Response({'ok': True, 'status': 200, 'provider': mock}, status=200)

        # If not configured to call real provider, return error
        if not api_url or not api_key:
            return Response({'error': 'retell not configured'}, status=503)

        try:
            headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
            payload = {'input': msg}
            # include optional model/agent keys if configured
            if api_model:
                payload['model'] = api_model
            if api_agent:
                payload['agent_id'] = api_agent

            r = requests.post(api_url, json=payload, headers=headers, timeout=15)
            # try to return provider response JSON (including error bodies) with original status
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}

            return Response({'ok': 200 <= r.status_code < 300, 'status': r.status_code, 'provider': data}, status=r.status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=502)


class RetellCreateWebCallView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Server-side proxy to Retell "Create Web Call" API.
        Docs: https://docs.retellai.com/api-references/create-web-call#create-web-call

        Accepts optional JSON body to override defaults:
        - agent_id (str)
        - agent_version (int)
        - metadata (object)
        - retell_llm_dynamic_variables (object)
        """
        api_key = getattr(settings, 'RETELL_API_KEY', None)
        # For web calls, only accept explicit agent_id or RETELL_CALL_AGENT_ID from settings
        agent_id = request.data.get('agent_id') or getattr(settings, 'RETELL_CALL_AGENT_ID', None)
        agent_version = request.data.get('agent_version', getattr(settings, 'RETELL_AGENT_VERSION', None))
        metadata = request.data.get('metadata') or {}
        dyn_vars = request.data.get('retell_llm_dynamic_variables') or {}
        create_url = getattr(settings, 'RETELL_CREATE_WEB_CALL_URL', 'https://api.retellai.com/v2/create-web-call')

        # Allow request to override mock for live testing
        def _to_bool(val):
            if isinstance(val, bool):
                return val
            if isinstance(val, (int, float)):
                return val != 0
            if isinstance(val, str):
                return val.strip().lower() in ('1', 'true', 't', 'yes', 'on')
            return False

        req_mock = request.data.get('mock', None)
        use_mock = getattr(settings, 'RETELL_MOCK', False) if req_mock is None else _to_bool(req_mock)
        if use_mock:
            mock = {
                'call_type': 'web_call',
                'access_token': 'dev_access_token',
                'call_id': 'dev_call_id',
                'agent_id': agent_id or 'dev_agent',
                'agent_version': int(agent_version) if agent_version else 1,
                'call_status': 'registered',
                'metadata': metadata,
                'retell_llm_dynamic_variables': dyn_vars,
            }
            return Response(mock, status=201)

        if not api_key or not agent_id:
            return Response({'error': 'retell not configured (missing API key or RETELL_CALL_AGENT_ID)'}, status=503)

        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            }
            payload = {
                'agent_id': agent_id,
            }
            if agent_version is not None and str(agent_version).strip() != '':
                try:
                    payload['agent_version'] = int(agent_version)
                except Exception:
                    pass
            if metadata:
                payload['metadata'] = metadata
            if dyn_vars:
                payload['retell_llm_dynamic_variables'] = dyn_vars
            # Include conversation memory context for the authenticated user if present
            try:
                if request.user and request.user.is_authenticated:
                    mem = ConversationMemory.objects.filter(user=request.user).order_by('-last_updated').first()
                    if mem and isinstance(mem.messages, list) and mem.messages:
                        payload.setdefault('retell_llm_dynamic_variables', {})
                        payload['retell_llm_dynamic_variables']['conversation_memory'] = mem.messages[-20:]
            except Exception:
                pass

            r = requests.post(create_url, json=payload, headers=headers, timeout=15)
            if not r.ok:
                # Fallback to v2 path explicitly if not already
                try:
                    alt = 'https://api.retellai.com/v2/create-web-call'
                    if create_url.rstrip('/') != alt:
                        r = requests.post(alt, json=payload, headers=headers, timeout=15)
                except Exception:
                    pass
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}
            return Response(data, status=r.status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=502)


class RetellListConversationFlowsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Simple HEAD-checked GET to Retell list-conversation-flows using the API key from .env.
        Pass optional ?limit=1000 and pagination params as-is.
        """
        api_key = getattr(settings, 'RETELL_API_KEY', None)
        url = getattr(settings, 'RETELL_LIST_CONVERSATION_FLOWS_URL', 'https://api.retellai.com/list-conversation-flows')
        if not api_key:
            return Response({'error': 'RETELL_API_KEY not configured'}, status=503)
        try:
            headers = { 'Authorization': f'Bearer {api_key}' }
            params = {}
            for k in ('limit', 'pagination_key', 'pagination_key_version'):
                v = request.query_params.get(k)
                if v:
                    params[k] = v
            r = requests.get(url, headers=headers, params=params or None, timeout=20)
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}
            return Response(data, status=r.status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=502)


class RetellListConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        api_key = getattr(settings, 'RETELL_API_KEY', None)
        url = getattr(settings, 'RETELL_LIST_CONVERSATIONS_URL', 'https://api.retellai.com/list-conversations')
        if not api_key:
            return Response({'error': 'RETELL_API_KEY not configured'}, status=503)
        try:
            headers = { 'Authorization': f'Bearer {api_key}' }
            params = {}
            for k in ('limit', 'pagination_key', 'pagination_key_version'):
                v = request.query_params.get(k)
                if v:
                    params[k] = v
            r = requests.get(url, headers=headers, params=params or None, timeout=20)
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}
            return Response(data, status=r.status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=502)


class RetellListCallsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        api_key = getattr(settings, 'RETELL_API_KEY', None)
        url = getattr(settings, 'RETELL_LIST_CALLS_URL', 'https://api.retellai.com/list-calls')
        if not api_key:
            return Response({'error': 'RETELL_API_KEY not configured'}, status=503)
        try:
            headers = { 'Authorization': f'Bearer {api_key}' }
            params = {}
            for k in ('limit', 'pagination_key', 'pagination_key_version'):
                v = request.query_params.get(k)
                if v:
                    params[k] = v
            r = requests.get(url, headers=headers, params=params or None, timeout=20)
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}
            return Response(data, status=r.status_code)
        except Exception as e:
            return Response({'error': str(e)}, status=502)


class ConversationMemoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_user(self, pk):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(pk=pk).first()

    def _check_access(self, request, target_user):
        if not target_user:
            return Response({'error': 'not found'}, status=404)
        if request.user.is_superuser:
            return None
        if target_user.id != request.user.id:
            return Response({'error': 'forbidden'}, status=403)
        return None

    def retrieve(self, request, pk=None):
        user = self._get_user(pk)
        err = self._check_access(request, user)
        if err:
            return err
        mem = ConversationMemory.objects.filter(user=user).order_by('-last_updated').first()
        if not mem:
            mem = ConversationMemory.objects.create(user=user)
        ser = ConversationMemorySerializer(mem)
        return Response(ser.data)

    def create(self, request, pk=None):
        user = self._get_user(pk)
        err = self._check_access(request, user)
        if err:
            return err
        mem = ConversationMemory.objects.filter(user=user).order_by('-last_updated').first()
        if not mem:
            mem = ConversationMemory.objects.create(user=user)
        payload = request.data if isinstance(request.data, dict) else {}
        role = (payload.get('role') or '').strip() or 'user'
        content = (payload.get('content') or '').strip()
        meta = payload.get('meta') if isinstance(payload.get('meta'), dict) else None
        mem.append_message(role, content, meta)
        return Response(ConversationMemorySerializer(mem).data, status=201)

    def destroy(self, request, pk=None):
        user = self._get_user(pk)
        err = self._check_access(request, user)
        if err:
            return err
        ConversationMemory.objects.filter(user=user).delete()
        return Response(status=204)


class RetellSyncWebhookView(APIView):
    """
    Sync endpoint with a complex token path to be used as a Retell callback.
    On each call, pulls conversations and calls from Retell and upserts CommSession records.
    Security: requires token to match settings.RETELL_SYNC_TOKEN. No session auth required.
    """
    authentication_classes = []
    permission_classes = []

    def _parse_iso(self, s):
        if not s:
            return None
        try:
            # Retell timestamps are ISO8601; handle 'Z' as UTC
            if s.endswith('Z'):
                s = s[:-1] + '+00:00'
            return datetime.fromisoformat(s)
        except Exception:
            return None

    def _status_from_retell(self, item):
        status = (item.get('status') or item.get('call_status') or item.get('conversation_status') or '').lower()
        mapping = {
            'completed': CommStatus.COMPLETED,
            'ended': CommStatus.COMPLETED,
            'failed': CommStatus.FAILED,
            'missed': CommStatus.MISSED,
            'canceled': CommStatus.CANCELED,
            'ongoing': CommStatus.ONGOING,
            'in_progress': CommStatus.ONGOING,
            'registered': CommStatus.ONGOING,
            'not_connected': CommStatus.ONGOING,
            'error': CommStatus.FAILED,
        }
        return mapping.get(status, CommStatus.ONGOING)

    def _parse_ms(self, ms_val):
        """Parse milliseconds-since-epoch into aware datetime (UTC)."""
        if not ms_val and ms_val != 0:
            return None
        try:
            ms = int(ms_val)
            return datetime.fromtimestamp(ms / 1000.0, tz=dt_timezone.utc)
        except Exception:
            return None

    def _stable_ref(self, item: dict, kind: str):
        """Create a stable external reference when provider IDs are missing."""
        import hashlib, json
        try:
            basis = {
                'kind': kind,
                'id': item.get('id') or item.get('uuid') or item.get('conversation_flow_id'),
                'start': item.get('start_time') or item.get('registered_time') or item.get('started_at'),
                'from': item.get('from') or item.get('customer_number'),
                'to': item.get('to') or item.get('agent_number'),
            }
            h = hashlib.sha1(json.dumps(basis, sort_keys=True).encode('utf-8')).hexdigest()
            return f"retell:{kind}:{h}"
        except Exception:
            return None

    def _upsert_session(self, user, base_defaults):
        # Upsert by unique retell ids preference: call_id, conversation_id, else external_ref
        call_id = base_defaults.get('retell_call_id')
        conv_id = base_defaults.get('retell_conversation_id')
        flow_id = base_defaults.get('conversation_flow_id')
        ext_ref = base_defaults.get('external_ref')
        lookup = {}
        if call_id:
            lookup['retell_call_id'] = call_id
        elif conv_id:
            lookup['retell_conversation_id'] = conv_id
        elif flow_id:
            lookup['conversation_flow_id'] = flow_id
        elif ext_ref:
            lookup['external_ref'] = ext_ref
        else:
            # no identifiers, skip
            return None, False

        obj, created = CommSession.objects.get_or_create(defaults=base_defaults, **lookup)
        if not created:
            # update mutable fields
            for f in (
                'status', 'started_at', 'ended_at', 'duration_sec', 'message_count', 'direction', 'channel',
                'intent', 'transcript_excerpt', 'from_identity', 'to_identity', 'metadata'
            ):
                val = base_defaults.get(f)
                if val is not None:
                    setattr(obj, f, val)
            obj.save()
        return obj, created

    def _build_detail_url(self, base_url, item_id):
        # ensure single slash join
        return f"{base_url.rstrip('/')}/{item_id}"

    def _extract_messages(self, detail):
        """Try to return a list of message dicts with keys: id, role, content, timestamp, audio_url, metadata"""
        if not isinstance(detail, dict):
            return []
        # Try common containers
        candidates = []
        for key in ('transcript_with_tool_calls', 'scrubbed_transcript_with_tool_calls', 'transcript_object', 'messages', 'turns', 'logs', 'transcript', 'events'):
            v = detail.get(key)
            if isinstance(v, list) and v:
                candidates = v
                break
        if not candidates and isinstance(detail.get('summary'), dict):
            # some APIs put a transcript list under summary.transcript
            v = detail['summary'].get('transcript')
            if isinstance(v, list):
                candidates = v

        out = []
        for i, m in enumerate(candidates):
            if not isinstance(m, dict):
                continue
            msg_id = m.get('id') or m.get('message_id') or m.get('uuid')
            role = (m.get('role') or m.get('speaker') or m.get('source') or '').lower()
            content = m.get('content') or m.get('text') or m.get('message') or m.get('utterance') or ''
            ts = m.get('timestamp') or m.get('time') or m.get('created_at') or m.get('time_created')
            # If timestamps are nested
            if not ts and isinstance(m.get('meta'), dict):
                ts = m['meta'].get('timestamp')
            audio_url = m.get('audio_url') or m.get('recording_url') or None
            # capture first word start offset if available
            offset_s = None
            words = m.get('words')
            if isinstance(words, list) and words:
                w0 = words[0]
                try:
                    offset_s = float(w0.get('start')) if w0 and w0.get('start') is not None else None
                except Exception:
                    offset_s = None
            out.append({
                'id': msg_id,
                'role': role or 'assistant' if i % 2 else 'user',
                'content': content,
                'timestamp': ts,
                'audio_url': audio_url,
                'offset_s': offset_s,
                'metadata': {k: v for k, v in m.items() if k not in (
                    'id','message_id','uuid','role','speaker','source','content','text','message','utterance',
                    'timestamp','time','created_at','time_created','audio_url','recording_url','words'
                )}
            })
        return out

    def _ensure_message(self, session, channel, msg_dict, created_counters):
        from .models import CommMessage, MessageRole, CommAttachment, CommSession, ConversationMemory
        # Parse timestamp
        ts = self._parse_iso(msg_dict.get('timestamp'))
        if not ts:
            # derive from offset if available
            off = msg_dict.get('offset_s')
            if off is not None and session.started_at:
                try:
                    ts = session.started_at + timedelta(seconds=float(off))
                except Exception:
                    ts = None
        ts = ts or datetime.now(dt_timezone.utc)
        role_raw = (msg_dict.get('role') or '').lower()
        role_map = {
            'user': MessageRole.USER,
            'assistant': MessageRole.ASSISTANT,
            'agent': MessageRole.AGENT,
            'system': MessageRole.SYSTEM,
            'caller': MessageRole.USER,
            'bot': MessageRole.ASSISTANT,
        }
        role = role_map.get(role_raw, MessageRole.ASSISTANT)
        content = (msg_dict.get('content') or '').strip()
        provider_msg_id = msg_dict.get('id')

        qs = CommMessage.objects.filter(session=session, channel=channel, timestamp=ts, role=role)
        if provider_msg_id:
            msg, created = CommMessage.objects.get_or_create(
                session=session,
                provider_msg_id=provider_msg_id,
                defaults={
                    'tenant': session.tenant,
                    'timestamp': ts,
                    'channel': channel,
                    'role': role,
                    'content': content,
                    'metadata': msg_dict.get('metadata') or {},
                }
            )
        else:
            # Fallback idempotency by ts/role/content prefix
            existing = qs.filter(content=content)[:1]
            if existing:
                msg = existing[0]
                created = False
            else:
                msg = CommMessage.objects.create(
                    session=session,
                    tenant=session.tenant,
                    timestamp=ts,
                    channel=channel,
                    role=role,
                    content=content,
                    metadata=msg_dict.get('metadata') or {},
                )
                created = True

        if created:
            created_counters['messages_created'] += 1
        else:
            # update content/metadata on subsequent syncs
            changed = False
            if content and content != (msg.content or ''):
                msg.content = content
                changed = True
            md = msg_dict.get('metadata') or {}
            if md and md != (msg.metadata or {}):
                msg.metadata = md
                changed = True
            if changed:
                msg.save()
                created_counters['messages_updated'] += 1

        # Attach audio if present
        audio_url = msg_dict.get('audio_url')
        if audio_url:
            has = msg.attachments.filter(storage_path=audio_url).exists()
            if not has:
                CommAttachment.objects.create(
                    message=msg,
                    tenant=session.tenant,
                    attach_type='audio',
                    storage_path=audio_url,
                    mime_type='audio/mpeg',
                )
                created_counters['attachments_created'] += 1

        # Also append to per-user memory if session has a user
        try:
            if session and session.user_id:
                cm = ConversationMemory.objects.filter(user_id=session.user_id).order_by('-last_updated').first()
                if not cm:
                    cm = ConversationMemory.objects.create(user_id=session.user_id)
                role_val = role.value if hasattr(role, 'value') else str(role)
                cm.append_message(role_val, content, {'session_id': str(session.tenant), 'provider_msg_id': provider_msg_id})
        except Exception:
            pass
        return msg

    def get(self, request, token=None):
        return self.post(request, token)

    def _fetch_paginated(self, base_url, headers, params, list_keys=("conversations", "calls", "data", "items"), max_pages=5):
        """Generic paginator for Retell list-* endpoints. Returns (items, debug).
        debug includes statuses and page counts for diagnostics.
        """
        items = []
        debug = { 'url': base_url, 'pages': [] }
        next_key = params.get('pagination_key') if params else None
        for i in range(max_pages):
            p = dict(params or {})
            if next_key:
                p['pagination_key'] = next_key
            # Ensure Accept header
            h = dict(headers or {})
            h.setdefault('Accept', 'application/json')
            r = requests.get(base_url, headers=h, params=p or None, timeout=20)
            page_info = { 'status': r.status_code }
            try:
                data = r.json()
            except ValueError:
                data = { 'text': r.text }
            page_info['keys'] = [k for k in (list_keys or ()) if isinstance(data, dict) and k in data]
            debug['pages'].append(page_info)
            if not (200 <= r.status_code < 300):
                break
            # Extract list
            chunk = None
            if isinstance(data, list):
                chunk = data
            elif isinstance(data, dict):
                for k in list_keys:
                    v = data.get(k)
                    if isinstance(v, list):
                        chunk = v
                        break
            if chunk:
                items.extend(chunk)
            # find pagination key for next page
            next_key = None
            if isinstance(data, dict):
                next_key = data.get('next_pagination_key') or data.get('pagination_key')
            if not next_key:
                break
        debug['total'] = len(items)
        return items, debug

    def _list_calls_post(self, url, headers, limit=1000, pagination_key=None):
        """Call Retell list-calls via POST as per current docs.
        Returns (items, debug) where items is a list of calls.
        """
        h = dict(headers or {})
        h.setdefault('Accept', 'application/json')
        h['Content-Type'] = 'application/json'
        payload = {'limit': int(limit)}
        if pagination_key:
            payload['pagination_key'] = pagination_key
        try:
            r = requests.post(url, headers=h, json=payload, timeout=30)
            dbg = {'url': url, 'status': r.status_code}
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}
            dbg['keys'] = list(data.keys()) if isinstance(data, dict) else ['list'] if isinstance(data, list) else []
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for k in ('calls','data','items'):
                    v = data.get(k)
                    if isinstance(v, list):
                        items = v
                        break
            dbg['total'] = len(items)
            return items, dbg
        except Exception as e:
            return [], {'url': url, 'error': str(e)}

    def _list_conversations_post(self, url, headers, limit=1000, pagination_key=None, extra_filters=None):
        """Call Retell list-conversations via POST (v2). Returns (items, debug)."""
        h = dict(headers or {})
        h.setdefault('Accept', 'application/json')
        h['Content-Type'] = 'application/json'
        payload = {'limit': int(limit)}
        if pagination_key:
            payload['pagination_key'] = pagination_key
        if isinstance(extra_filters, dict):
            payload.update({k: v for k, v in extra_filters.items() if v is not None})
        try:
            r = requests.post(url, headers=h, json=payload, timeout=30)
            dbg = {'url': url, 'status': r.status_code}
            try:
                data = r.json()
            except ValueError:
                data = {'text': r.text}
            dbg['keys'] = list(data.keys()) if isinstance(data, dict) else ['list'] if isinstance(data, list) else []
            items = []
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                for k in ('conversations','data','items'):
                    v = data.get(k)
                    if isinstance(v, list):
                        items = v
                        break
            dbg['total'] = len(items)
            return items, dbg
        except Exception as e:
            return [], {'url': url, 'error': str(e)}

    def post(self, request, token=None):
        expected = getattr(settings, 'RETELL_SYNC_TOKEN', None)
        if not expected or token != expected:
            return Response({'error': 'forbidden'}, status=403)

        api_key = getattr(settings, 'RETELL_API_KEY', None)
        if not api_key:
            return Response({'error': 'retell not configured'}, status=503)

        headers = {'Authorization': f'Bearer {api_key}'}

        created = 0
        updated = 0
        errors = []
        stats = {
            'messages_created': 0,
            'messages_updated': 0,
            'attachments_created': 0,
        }

        diag = {}

    # Fetch conversations (try multiple candidate endpoints with pagination)
        try:
            conv_candidates = []
            conv_candidates.append(getattr(settings, 'RETELL_LIST_CONVERSATIONS_URL', 'https://api.retellai.com/list-conversations'))
            if getattr(settings, 'RETELL_LIST_CONVERSATIONS_V2_URL', None):
                conv_candidates.append(getattr(settings, 'RETELL_LIST_CONVERSATIONS_V2_URL'))
            conv_candidates += [
                'https://api.retellai.com/v2/list-conversations',
                'https://api.retellai.com/v2/conversations',
                'https://api.retellai.com/conversations',
            ]
            conversations = []
            conv_attempts = []
            for url in conv_candidates:
                try:
                    conv_list, conv_dbg = self._fetch_paginated(url, headers, {'limit': 1000}, list_keys=("conversations","data"))
                    conv_attempts.append({'url': url, **conv_dbg})
                    if conv_list:
                        conversations = conv_list
                        break
                except Exception as ie:
                    conv_attempts.append({'url': url, 'error': str(ie)})
            # If empty, try POST fallback for conversations (v2)
            if not conversations:
                post_candidates = [
                    getattr(settings, 'RETELL_LIST_CONVERSATIONS_V2_URL', 'https://api.retellai.com/v2/list-conversations'),
                    'https://api.retellai.com/list-conversations',
                ]
                for purl in post_candidates:
                    items, dbg = self._list_conversations_post(purl, headers, limit=1000)
                    conv_attempts.append({'method': 'POST', **dbg})
                    if items:
                        conversations = items
                        break
            diag['conversations_list'] = {'attempts': conv_attempts, 'total': len(conversations)}
            # record item shape
            try:
                first = conversations[0] if conversations else None
                if isinstance(first, dict):
                    diag['conversations_first_keys'] = sorted(list(first.keys()))
            except Exception:
                pass
            # If still empty, try fetching via conversation flows (flow-scoped)
            if not conversations:
                flows_diag = {'attempts': []}
                try:
                    flows_url = getattr(settings, 'RETELL_LIST_CONVERSATION_FLOWS_URL', 'https://api.retellai.com/list-conversation-flows')
                    fr = requests.get(flows_url, headers=headers, params={'limit': 100}, timeout=20)
                    flows_data = fr.json() if fr.ok else []
                    if isinstance(flows_data, list):
                        flows = flows_data
                    elif isinstance(flows_data, dict):
                        flows = flows_data.get('conversation_flows') or flows_data.get('data') or flows_data.get('items') or []
                    else:
                        flows = []
                    flows_diag['status'] = fr.status_code
                    flows_diag['count'] = len(flows)
                except Exception as e:
                    flows = []
                    flows_diag['error'] = str(e)
                # Try per-flow conversation listing using filters and path-style endpoints
                collected = []
                for flow in (flows or [])[:10]:
                    flow_id = flow.get('conversation_flow_id') or flow.get('id')
                    if not flow_id:
                        continue
                    # 1) Filtered list-conversations ...?conversation_flow_id=FLOW
                    for url in conv_candidates:
                        try:
                            clist, cdbg = self._fetch_paginated(url, headers, {'limit': 1000, 'conversation_flow_id': flow_id}, list_keys=("conversations","data"))
                            flows_diag['attempts'].append({'flow_id': flow_id, 'url': url, **cdbg})
                            if clist:
                                collected.extend(clist)
                                break
                        except Exception as ie:
                            flows_diag['attempts'].append({'flow_id': flow_id, 'url': url, 'error': str(ie)})
                    # 2) Path-style endpoints: /conversation-flows/{id}/conversations (v1 and v2)
                    for purl in [
                        f"https://api.retellai.com/conversation-flows/{flow_id}/conversations",
                        f"https://api.retellai.com/v2/conversation-flows/{flow_id}/conversations",
                    ]:
                        try:
                            rr = requests.get(purl, headers=headers, timeout=20)
                            pdata = rr.json() if rr.ok else {}
                            keys = []
                            if isinstance(pdata, list):
                                collected.extend(pdata)
                            elif isinstance(pdata, dict):
                                for kk in ("conversations","data","items"):
                                    v = pdata.get(kk)
                                    if isinstance(v, list):
                                        collected.extend(v)
                                        keys.append(kk)
                            flows_diag['attempts'].append({'flow_id': flow_id, 'url': purl, 'status': rr.status_code, 'keys': keys})
                        except Exception as ie:
                            flows_diag['attempts'].append({'flow_id': flow_id, 'url': purl, 'error': str(ie)})
                if collected:
                    conversations = collected
                diag['conversations_flows'] = flows_diag
        except Exception as e:
            conversations = []
            errors.append(f'conversations: {e}')

        # Fetch calls (try multiple candidate endpoints with pagination)
        try:
            call_candidates = []
            call_candidates.append(getattr(settings, 'RETELL_LIST_CALLS_URL', 'https://api.retellai.com/list-calls'))
            if getattr(settings, 'RETELL_LIST_CALLS_V2_URL', None):
                call_candidates.append(getattr(settings, 'RETELL_LIST_CALLS_V2_URL'))
            call_candidates += [
                'https://api.retellai.com/v2/list-calls',
                'https://api.retellai.com/v2/calls',
                'https://api.retellai.com/calls',
            ]
            calls = []
            call_attempts = []
            for url in call_candidates:
                try:
                    calls_list, calls_dbg = self._fetch_paginated(url, headers, {'limit': 1000}, list_keys=("calls","data","items"))
                    call_attempts.append({'url': url, **calls_dbg})
                    if calls_list:
                        calls = calls_list
                        break
                except Exception as ie:
                    call_attempts.append({'url': url, 'error': str(ie)})
            # If still empty, try POST /v2/list-calls specifically as per docs
            if not calls:
                post_candidates = [
                    getattr(settings, 'RETELL_LIST_CALLS_V2_URL', 'https://api.retellai.com/v2/list-calls'),
                    'https://api.retellai.com/list-calls',
                ]
                for purl in post_candidates:
                    items, dbg = self._list_calls_post(purl, headers, limit=1000)
                    call_attempts.append({'method': 'POST', **dbg})
                    if items:
                        calls = items
                        break
            diag['calls_list'] = {'attempts': call_attempts, 'total': len(calls)}
            try:
                first = calls[0] if calls else None
                if isinstance(first, dict):
                    diag['calls_first_keys'] = sorted(list(first.keys()))
            except Exception:
                pass
            # If still empty, try flow-scoped and agent-scoped fallbacks
            if not calls:
                calls_flows_diag = {'attempts': []}
                # Reuse flows fetched above if available; otherwise try to fetch few
                flows = []
                try:
                    flows_url = getattr(settings, 'RETELL_LIST_CONVERSATION_FLOWS_URL', 'https://api.retellai.com/list-conversation-flows')
                    fr = requests.get(flows_url, headers=headers, params={'limit': 50}, timeout=20)
                    flows_data = fr.json() if fr.ok else []
                    if isinstance(flows_data, list):
                        flows = flows_data
                    elif isinstance(flows_data, dict):
                        flows = flows_data.get('conversation_flows') or flows_data.get('data') or flows_data.get('items') or []
                    calls_flows_diag['status'] = fr.status_code
                    calls_flows_diag['count'] = len(flows)
                except Exception as e:
                    calls_flows_diag['error'] = str(e)
                collected = []
                for flow in (flows or [])[:10]:
                    flow_id = flow.get('conversation_flow_id') or flow.get('id')
                    if not flow_id:
                        continue
                    # Path-style: /conversation-flows/{id}/calls
                    for purl in [
                        f"https://api.retellai.com/conversation-flows/{flow_id}/calls",
                        f"https://api.retellai.com/v2/conversation-flows/{flow_id}/calls",
                    ]:
                        try:
                            rr = requests.get(purl, headers=headers, timeout=20)
                            pdata = rr.json() if rr.ok else {}
                            keys = []
                            if isinstance(pdata, list):
                                collected.extend(pdata)
                            elif isinstance(pdata, dict):
                                for kk in ("calls","data","items"):
                                    v = pdata.get(kk)
                                    if isinstance(v, list):
                                        collected.extend(v)
                                        keys.append(kk)
                            calls_flows_diag['attempts'].append({'flow_id': flow_id, 'url': purl, 'status': rr.status_code, 'keys': keys})
                        except Exception as ie:
                            calls_flows_diag['attempts'].append({'flow_id': flow_id, 'url': purl, 'error': str(ie)})
                # Agent filter (if provided)
                agent_id = getattr(settings, 'RETELL_CALL_AGENT_ID', None) or getattr(settings, 'RETELL_AGENT_ID', None)
                if agent_id and not collected:
                    for url in call_candidates:
                        try:
                            clist, cdbg = self._fetch_paginated(url, headers, {'limit': 1000, 'agent_id': agent_id}, list_keys=("calls","data"))
                            calls_flows_diag['attempts'].append({'agent_id': agent_id, 'url': url, **cdbg})
                            if clist:
                                collected.extend(clist)
                                break
                        except Exception as ie:
                            calls_flows_diag['attempts'].append({'agent_id': agent_id, 'url': url, 'error': str(ie)})
                if collected:
                    calls = collected
                diag['calls_flows'] = calls_flows_diag
        except Exception as e:
            calls = []
            errors.append(f'calls: {e}')

        # Use system user or leave null; here we leave null, later we can map by metadata
        user = None

        # Upsert conversations
        skipped_no_id = 0
        for c in conversations:
            try:
                started = self._parse_iso(c.get('start_time') or c.get('started_at'))
                ended = self._parse_iso(c.get('end_time') or c.get('ended_at'))
                duration = None
                if started and ended:
                    duration = int((ended - started).total_seconds())
                external_ref = None
                if not (c.get('conversation_id') or c.get('id') or c.get('conversation_flow_id') or (isinstance(c.get('conversation_flow'), dict) and c['conversation_flow'].get('id'))):
                    external_ref = self._stable_ref(c, 'conversation')
                defaults = {
                    'user': user,
                    # Conversations represent web/chat sessions in our model
                    'channel': Channel.WEB,
                    'direction': Direction.OUTBOUND,
                    'status': self._status_from_retell(c),
                    'provider': 'retell',
                    'retell_conversation_id': c.get('conversation_id') or c.get('id'),
                    'conversation_flow_id': c.get('conversation_flow_id') or (c.get('conversation_flow') or {}).get('id') if isinstance(c.get('conversation_flow'), dict) else None,
                    'external_ref': external_ref,
                    'started_at': started or datetime.now(dt_timezone.utc),
                    'ended_at': ended,
                    'duration_sec': duration or 0,
                    'message_count': c.get('message_count') or 0,
                    'intent': (c.get('summary') or {}).get('intent') if isinstance(c.get('summary'), dict) else None,
                    'transcript_excerpt': (c.get('summary') or {}).get('overall') if isinstance(c.get('summary'), dict) else None,
                    'from_identity': c.get('from') or c.get('customer_number'),
                    'to_identity': c.get('to') or c.get('agent_number'),
                    'metadata': c.get('metadata') or {},
                    'provider_payload': c,
                }
                obj, was_created = self._upsert_session(user, defaults)
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append(f"conversation upsert: {e}")

        # Upsert calls
        for k in calls:
            try:
                # Retell V2 list-calls uses ms timestamps
                started = self._parse_ms(k.get('start_timestamp')) or self._parse_iso(k.get('start_time') or k.get('registered_time') or k.get('started_at'))
                ended = self._parse_ms(k.get('end_timestamp')) or self._parse_iso(k.get('end_time') or k.get('ended_at'))
                duration_ms = k.get('duration_ms')
                duration = None
                if isinstance(duration_ms, (int, float)):
                    duration = max(0, int(float(duration_ms) / 1000.0))
                elif started and ended:
                    duration = int((ended - started).total_seconds())
                # Direction mapping if present
                dir_raw = (k.get('direction') or '').lower()
                direction = Direction.INBOUND if dir_raw in ('inbound','incoming') else Direction.OUTBOUND
                # Message count and excerpt hints
                transcript_list = k.get('transcript_object') or []
                transcript_text = k.get('transcript') or ''
                call_summary = None
                ca = k.get('call_analysis') or {}
                if isinstance(ca, dict):
                    call_summary = ca.get('call_summary')
                defaults = {
                    'user': user,
                    'channel': Channel.VOICE,
                    'direction': direction,
                    'status': self._status_from_retell(k),
                    'provider': 'retell',
                    'retell_call_id': k.get('call_id') or k.get('id'),
                    'started_at': started or datetime.now(dt_timezone.utc),
                    'ended_at': ended,
                    'duration_sec': (duration or 0),
                    'message_count': len(transcript_list) if isinstance(transcript_list, list) else (k.get('message_count') or 0),
                    'intent': None,
                    'transcript_excerpt': (call_summary or (transcript_text[:180] if transcript_text else None)),
                    'from_identity': k.get('from') or k.get('customer_number'),
                    'to_identity': k.get('to') or k.get('agent_number'),
                    'metadata': k.get('metadata') or {},
                    'provider_payload': k,
                }
                obj, was_created = self._upsert_session(user, defaults)
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append(f"call upsert: {e}")

        # Fetch details and persist messages for conversations
        conv_base = getattr(settings, 'RETELL_GET_CONVERSATION_URL', 'https://api.retellai.com/get-conversation')
        for c in conversations:
            try:
                conv_id = c.get('conversation_id') or c.get('id')
                if not conv_id:
                    continue
                # Newer API style uses query param instead of path segment
                d_resp = requests.get(conv_base, headers=headers, params={'conversation_id': conv_id}, timeout=20)
                if not d_resp.ok:
                    # Fallback to older v2 path style if configured
                    try:
                        v2_base = getattr(settings, 'RETELL_LIST_CONVERSATIONS_URL', '')
                        if '/v2/conversations' in v2_base:
                            detail_url = self._build_detail_url(v2_base, conv_id)
                            d_resp = requests.get(detail_url, headers=headers, timeout=20)
                    except Exception:
                        pass
                if not d_resp.ok:
                    continue
                detail = d_resp.json()
                # Find the session we just upserted
                session = CommSession.objects.filter(retell_conversation_id=conv_id).first()
                if not session:
                    continue
                # Extract messages and persist
                for m in self._extract_messages(detail):
                    self._ensure_message(session, Channel.WEB, m, stats)
                # Save provider payload for detail
                session.provider_payload = detail if isinstance(detail, dict) else { 'raw': detail }
                # Update aggregates if available
                summary = detail.get('summary') if isinstance(detail, dict) else None
                if isinstance(summary, dict):
                    intent = summary.get('intent')
                    overall = summary.get('overall')
                    if intent and intent != session.intent:
                        session.intent = intent
                    if overall and overall != (session.transcript_excerpt or ''):
                        session.transcript_excerpt = overall
                # Update tokens/cost if available
                usage = detail.get('usage') if isinstance(detail, dict) else None
                if isinstance(usage, dict):
                    pt = usage.get('prompt_tokens') or 0
                    ct = usage.get('completion_tokens') or 0
                    session.tokens_prompt = pt
                    session.tokens_completion = ct
                cost = detail.get('cost_usd')
                if isinstance(cost, (int, float)):
                    session.cost_usd = cost
                session.message_count = session.messages.count()
                if session.duration_sec and session.duration_sec > 0:
                    session.voice_minutes = round(session.duration_sec / 60.0, 2)
                session.save()
            except Exception as e:
                errors.append(f"conversation detail: {e}")

        # Fetch details and persist messages for calls (if API provides transcript/messages)
        calls_base = getattr(settings, 'RETELL_GET_CALL_URL', 'https://api.retellai.com/get-call')
        for k in calls:
            try:
                call_id = k.get('call_id') or k.get('id')
                if not call_id:
                    continue
                # Try query param first
                h = dict(headers or {})
                h.setdefault('Accept', 'application/json')
                d_resp = requests.get(calls_base, headers=h, params={'call_id': call_id}, timeout=20)
                if not d_resp.ok:
                    # Fallback to explicit path variants
                    try:
                        v2_get = 'https://api.retellai.com/v2/get-call'
                        detail_url = self._build_detail_url(v2_get, call_id)
                        d_resp = requests.get(detail_url, headers=h, timeout=20)
                        if not d_resp.ok:
                            get_legacy = 'https://api.retellai.com/get-call'
                            detail_url = self._build_detail_url(get_legacy, call_id)
                            d_resp = requests.get(detail_url, headers=h, timeout=20)
                    except Exception:
                        pass
                if not d_resp.ok:
                    continue
                detail = d_resp.json()
                session = CommSession.objects.filter(retell_call_id=call_id).first()
                if not session:
                    continue
                for m in self._extract_messages(detail):
                    self._ensure_message(session, Channel.VOICE, m, stats)
                # Similar aggregates
                session.provider_payload = detail if isinstance(detail, dict) else { 'raw': detail }
                session.message_count = session.messages.count()
                if session.duration_sec and session.duration_sec > 0:
                    session.voice_minutes = round(session.duration_sec / 60.0, 2)
                session.save()
            except Exception as e:
                errors.append(f"call detail: {e}")

        diag['skipped_no_id'] = skipped_no_id
        return Response({'ok': True, 'created': created, 'updated': updated, **stats, 'errors': errors, 'diag': diag, 'counts': {'conversations': len(conversations), 'calls': len(calls)}})


@method_decorator(login_required, name='dispatch')
class CommSessionListView(ListView):
    template_name = 'communications/session_list.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = CommSession.objects.all().order_by('-started_at')
        else:
            qs = CommSession.objects.filter(user=user).order_by('-started_at')
        q = self.request.GET.get('q', '').strip()
        channel = self.request.GET.get('channel', '').strip()
        status = self.request.GET.get('status', '').strip()
        direction = self.request.GET.get('direction', '').strip()
        if q:
            qs = qs.filter(
                Q(retell_call_id__icontains=q) |
                Q(retell_conversation_id__icontains=q) |
                Q(external_ref__icontains=q) |
                Q(intent__icontains=q) |
                Q(transcript_excerpt__icontains=q) |
                Q(from_identity__icontains=q) |
                Q(to_identity__icontains=q)
            )
        if channel:
            qs = qs.filter(channel=channel)
        if status:
            qs = qs.filter(status=status)
        if direction:
            qs = qs.filter(direction=direction)
        # Backfill tokens for objects in first page if missing
        try:
            sample = list(qs[:self.paginate_by])
            dirty = []
            for s in sample:
                if s.tokens_prompt == 0 and s.tokens_completion == 0 and s.transcript_excerpt:
                    s.tokens_prompt = max(1, len(s.transcript_excerpt.split()))
                    dirty.append(s)
            if dirty:
                from django.db import transaction
                with transaction.atomic():
                    for o in dirty:
                        o.save(update_fields=['tokens_prompt','updated_at'])
        except Exception:
            pass
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['channels'] = Channel.choices
        ctx['statuses'] = CommStatus.choices
        ctx['directions'] = Direction.choices
        ctx['q'] = self.request.GET.get('q', '')
        ctx['sel_channel'] = self.request.GET.get('channel', '')
        ctx['sel_status'] = self.request.GET.get('status', '')
        ctx['sel_direction'] = self.request.GET.get('direction', '')
        return ctx


@method_decorator(login_required, name='dispatch')
class CommSessionTablePartialView(ListView):
    template_name = 'communications/_sessions_table_body.html'
    context_object_name = 'sessions'
    paginate_by = 20

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            qs = CommSession.objects.all().order_by('-started_at')
        else:
            qs = CommSession.objects.filter(user=user).order_by('-started_at')
        q = self.request.GET.get('q', '').strip()
        channel = self.request.GET.get('channel', '').strip()
        status = self.request.GET.get('status', '').strip()
        direction = self.request.GET.get('direction', '').strip()
        if q:
            qs = qs.filter(
                Q(retell_call_id__icontains=q) |
                Q(retell_conversation_id__icontains=q) |
                Q(external_ref__icontains=q) |
                Q(intent__icontains=q) |
                Q(transcript_excerpt__icontains=q) |
                Q(from_identity__icontains=q) |
                Q(to_identity__icontains=q)
            )
        if channel:
            qs = qs.filter(channel=channel)
        if status:
            qs = qs.filter(status=status)
        if direction:
            qs = qs.filter(direction=direction)
        return qs


class CommSyncTriggerView(View):
    """Superuser-only site endpoint to trigger Retell sync without exposing the token to the client."""
    @method_decorator(login_required)
    def get(self, request):
        if not request.user.is_superuser:
            return HttpResponseForbidden("forbidden")
        token = getattr(settings, 'RETELL_SYNC_TOKEN', None)
        if not token:
            data = { 'ok': False, 'error': 'missing RETELL_SYNC_TOKEN' }
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(data, status=500)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        # Measure and log
        start = time.time()
        factory = APIRequestFactory()
        req = factory.get('/')
        resp = RetellSyncWebhookView.as_view()(req, token=token)
        duration_ms = int((time.time() - start) * 1000)
        # Normalize
        payload = getattr(resp, 'data', None)
        status = getattr(resp, 'status_code', 200)

        # Persist sync log
        try:
            from .models import CommSyncLog
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()
            if not ip:
                ip = request.META.get('REMOTE_ADDR')
            CommSyncLog.objects.create(
                user=request.user,
                ip=ip,
                status_code=int(status or 0),
                duration_ms=duration_ms,
                payload=payload or { 'status': status },
            )
        except Exception:
            pass
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse(payload or { 'status': status }, status=status)
        # Non-AJAX: redirect back
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


@login_required
@require_GET
def latest_sync_log(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("forbidden")
    try:
        from .models import CommSyncLog
        obj = CommSyncLog.objects.order_by('-created_at').first()
        if not obj:
            return JsonResponse({'ok': False, 'error': 'no logs'}, status=404)
        return JsonResponse({
            'ok': True,
            'created_at': obj.created_at.isoformat(),
            'user': obj.user.username if obj.user else None,
            'ip': obj.ip,
            'status_code': obj.status_code,
            'duration_ms': obj.duration_ms,
            'payload': obj.payload,
        })
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)


class RetellSyncNowView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'forbidden'}, status=403)
        start = time.time()
        result = refresh_retell_sessions()
        duration_ms = int((time.time() - start) * 1000)
        # persist log
        try:
            from .models import CommSyncLog
            ip = request.META.get('HTTP_X_FORWARDED_FOR')
            if ip and ',' in ip:
                ip = ip.split(',')[0].strip()
            if not ip:
                ip = request.META.get('REMOTE_ADDR')
            CommSyncLog.objects.create(
                user=request.user,
                ip=ip,
                status_code=200,
                duration_ms=duration_ms,
                payload=result,
            )
        except Exception:
            pass
        return Response(result, status=200)


class RetellSimulateConversationView(APIView):
    """Superuser-only endpoint to create a test WEB conversation with a couple of messages."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response({'error': 'forbidden'}, status=403)
        try:
            now = datetime.now(dt_timezone.utc)
            conv_id = f"conv_test_{int(time.time())}"
            helper = RetellSyncWebhookView()
            defaults = {
                'user': None,
                'channel': Channel.WEB,
                'direction': Direction.OUTBOUND,
                'status': CommStatus.COMPLETED,
                'provider': 'retell',
                'retell_conversation_id': conv_id,
                'conversation_flow_id': None,
                'started_at': now,
                'ended_at': now + timedelta(seconds=5),
                'duration_sec': 5,
                'message_count': 0,
                'intent': 'demo',
                'transcript_excerpt': 'Conversación de prueba',
                'from_identity': None,
                'to_identity': None,
                'metadata': {'test': True},
                'provider_payload': {'conversation_id': conv_id, 'test': True},
            }
            session, created = helper._upsert_session(None, defaults)
            stats = {'messages_created': 0, 'messages_updated': 0, 'attachments_created': 0}
            # Two sample messages
            helper._ensure_message(session, Channel.WEB, {
                'id': f'{conv_id}_m1',
                'role': 'user',
                'content': 'Hola, esto es una prueba.',
                'timestamp': now.isoformat(),
            }, stats)
            helper._ensure_message(session, Channel.WEB, {
                'id': f'{conv_id}_m2',
                'role': 'assistant',
                'content': '¡Hola! Todo listo. 😊',
                'timestamp': (now + timedelta(seconds=2)).isoformat(),
            }, stats)
            session.message_count = session.messages.count()
            session.save()
            return Response({'ok': True, 'session_id': session.id, 'retell_conversation_id': conv_id})
        except Exception as e:
            return Response({'ok': False, 'error': str(e)}, status=500)


class RetellSimpleCallbackView(APIView):
    """
    Simple webhook callback at /api/callback.
    - Verifies a shared secret in Authorization: Bearer <RETELL_WEBHOOK_TOKEN> (or X-Retell-Token header)
    - Accepts JSON with either call_id or conversation_id
    - Fetches details from Retell and upserts a single CommSession + messages
    - Returns 200 quickly without requiring authentication
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        expected = getattr(settings, 'RETELL_WEBHOOK_TOKEN', None) or getattr(settings, 'RETELL_SYNC_TOKEN', None)
        authz = request.headers.get('Authorization', '')
        header_token = None
        if authz.lower().startswith('bearer '):
            header_token = authz.split(' ', 1)[1].strip()
        if not header_token:
            header_token = request.headers.get('X-Retell-Token')
        if not expected or header_token != expected:
            return Response({'error': 'forbidden'}, status=403)

        api_key = getattr(settings, 'RETELL_API_KEY', None)
        if not api_key:
            return Response({'error': 'retell not configured'}, status=503)

        payload = request.data if isinstance(request.data, dict) else {}
        # Normalize top-level call/conversation identifiers
        root_call = payload.get('call') if isinstance(payload.get('call'), dict) else None
        root_conversation = payload.get('conversation') if isinstance(payload.get('conversation'), dict) else None
        call_id = payload.get('call_id') or (root_call or {}).get('call_id') or payload.get('id')
        conversation_id = payload.get('conversation_id') or (root_conversation or {}).get('conversation_id') or (payload.get('id') if (payload.get('type') or '').startswith('conversation') else None)

        helper = RetellSyncWebhookView()
        headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}
        stats = {'created': 0, 'updated': 0, 'messages_created': 0, 'messages_updated': 0, 'attachments_created': 0}

        # Prefer call update (faster, richer for voice)
        if call_id:
            try:
                # Prefer detail directly from payload if present
                detail = None
                for obj in (root_call, payload):
                    if isinstance(obj, dict):
                        if any(k in obj for k in ('transcript_object','messages','turns','events','transcript')):
                            detail = obj
                            break
                if detail is None:
                    base = getattr(settings, 'RETELL_GET_CALL_URL', 'https://api.retellai.com/get-call')
                    r = requests.get(base, headers=headers, params={'call_id': call_id}, timeout=20)
                    if not r.ok:
                        v2 = 'https://api.retellai.com/v2/get-call'
                        r = requests.get(f"{v2.rstrip('/')}/{call_id}", headers=headers, timeout=20)
                    if not r.ok:
                        return Response({'ok': False, 'call_id': call_id, 'error': 'not found'}, status=404)
                    detail = r.json()
                # Map fields similar to list-calls
                started = helper._parse_ms(detail.get('start_timestamp')) or helper._parse_iso(detail.get('start_time') or detail.get('registered_time') or detail.get('started_at'))
                ended = helper._parse_ms(detail.get('end_timestamp')) or helper._parse_iso(detail.get('end_time') or detail.get('ended_at'))
                dur = None
                dms = detail.get('duration_ms')
                if isinstance(dms, (int, float)):
                    dur = max(0, int(float(dms) / 1000.0))
                elif started and ended:
                    dur = int((ended - started).total_seconds())
                dir_raw = (detail.get('direction') or '').lower()
                direction = Direction.INBOUND if dir_raw in ('inbound','incoming') else Direction.OUTBOUND
                transcript_list = detail.get('transcript_object') or []
                transcript_text = detail.get('transcript') or ''
                session, was_created = _ingest_call_session(detail)
                if was_created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
                # messages
                for m in helper._extract_messages(detail):
                    helper._ensure_message(session, Channel.VOICE, m, stats)
                session.message_count = session.messages.count()
                if session.duration_sec and session.duration_sec > 0:
                    session.voice_minutes = round(session.duration_sec / 60.0, 2)
                session.save()
                return Response({'ok': True, 'call_id': call_id, **stats})
            except Exception as e:
                return Response({'ok': False, 'call_id': call_id, 'error': str(e)}, status=500)

        # Conversation fallback
        if conversation_id:
            try:
                # Prefer detail from webhook payload if present
                detail = None
                for obj in (root_conversation, payload):
                    if isinstance(obj, dict):
                        if any(k in obj for k in ('messages','transcript','turns','events','transcript_object')) or any(k in obj for k in ('start_time','started_at','end_time','ended_at')):
                            detail = obj
                            break
                if detail is None:
                    base = getattr(settings, 'RETELL_GET_CONVERSATION_URL', 'https://api.retellai.com/get-conversation')
                    r = requests.get(base, headers=headers, params={'conversation_id': conversation_id}, timeout=20)
                    if not r.ok:
                        v2 = getattr(settings, 'RETELL_LIST_CONVERSATIONS_URL', '')
                        if '/v2/conversations' in v2:
                            r = requests.get(f"{v2.rstrip('/')}/{conversation_id}", headers=headers, timeout=20)
                    if not r.ok:
                        return Response({'ok': False, 'conversation_id': conversation_id, 'error': 'not found'}, status=404)
                    detail = r.json()
                session, was_created = _ingest_chat_session(detail)
                if was_created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
                # messages
                for m in helper._extract_messages(detail):
                    helper._ensure_message(session, Channel.WEB, m, stats)
                session.message_count = session.messages.count()
                session.save()
                try:
                    refresh_retell_sessions(lite=True)
                except Exception:
                    pass
                return Response({'ok': True, 'conversation_id': conversation_id, **stats})
            except Exception as e:
                return Response({'ok': False, 'conversation_id': conversation_id, 'error': str(e)}, status=500)

        return Response({'ok': True, 'ignored': 'no call_id or conversation_id'}, status=200)


def resolve_user_from_payload(payload: dict):
    """Resolve a Django user from Retell payload.
    Tries payload.user_id, payload.customer_id, or metadata phone/email.
    TODO: Adjust mapping to your exact Retell fields.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not isinstance(payload, dict):
        return None
    # Direct id
    uid = payload.get('user_id') or payload.get('customer_id') or (payload.get('metadata') or {}).get('user_id')
    if uid:
        u = User.objects.filter(pk=uid).first()
        if u:
            return u
    # Email
    email = (payload.get('email') or (payload.get('metadata') or {}).get('email') or '').strip().lower()
    if email:
        u = User.objects.filter(email__iexact=email).first()
        if u:
            return u
    # Phone (very basic normalization)
    phone = (payload.get('phone') or (payload.get('metadata') or {}).get('phone') or '').strip()
    if phone:
        # If you store phone in profile, adjust accordingly
        u = User.objects.filter(username__icontains=phone).first()
        if u:
            return u
    return None


"""Deprecated mirror_conversation_to_comm_session removed: unified model CommSession is now source of truth."""


# --- Unified ingestion helpers (chat & call) ---
def _ingest_chat_session(item: dict):
    """Create or update a CommSession for a chat conversation item from Retell."""
    if not isinstance(item, dict):
        return None, False
    from .models import CommSession, Channel, Direction, CommStatus
    def parse_iso(s):
        if not s:
            return None
        try:
            if isinstance(s, (int, float)):
                from datetime import datetime, timezone
                return datetime.fromtimestamp(float(s)/1000.0, tz=timezone.utc)
            if isinstance(s, str) and s.endswith('Z'):
                s = s[:-1] + '+00:00'
            from datetime import datetime
            return datetime.fromisoformat(s)
        except Exception:
            return None
    def parse_ms(ms):
        if ms is None:
            return None
        try:
            return datetime.fromtimestamp(int(ms)/1000.0, tz=dt_timezone.utc)
        except Exception:
            return None

    conv_id = item.get('conversation_id') or item.get('id') or item.get('chat_id')
    if not conv_id:
        return None, False

    # New chat API (list-chats) uses start_timestamp (ms) and chat_status + chat_analysis
    is_new_chat_payload = 'chat_id' in item or 'chat_status' in item
    if is_new_chat_payload:
        started = parse_ms(item.get('start_timestamp')) or parse_iso(item.get('start_time') or item.get('started_at'))
        ended = None  # API doesn't always return end timestamp; treat ended if status indicates closure
        raw_status = (item.get('chat_status') or '').lower()
        status_map = {
            'ended': CommStatus.COMPLETED,
            'completed': CommStatus.COMPLETED,
            'failed': CommStatus.FAILED,
            'canceled': CommStatus.CANCELED,
            'cancelled': CommStatus.CANCELED,
            'ongoing': CommStatus.ONGOING,
            'in_progress': CommStatus.ONGOING,
        }
        status_val = status_map.get(raw_status, CommStatus.ONGOING)
        # If ended but we have no explicit end time, approximate with started
        if status_val == CommStatus.COMPLETED and not ended:
            ended = started
        transcript_text = (item.get('chat_analysis') or {}).get('chat_summary') or item.get('transcript') or None
        msg_list = item.get('message_with_tool_calls') or item.get('messages') or []
        msg_count = len(msg_list) if isinstance(msg_list, list) else 0
        defaults = {
            'user': None,
            'channel': Channel.WEB,
            'direction': Direction.OUTBOUND,
            'status': status_val,
            'provider': 'retell',
            'retell_conversation_id': conv_id,
            'started_at': started or datetime.now(dt_timezone.utc),
            'ended_at': ended,
            'duration_sec': 0,
            'message_count': msg_count,
            'intent': None,  # no direct intent field in new payload
            'transcript_excerpt': (transcript_text[:300] if transcript_text else None),
            'from_identity': None,
            'to_identity': None,
            'metadata': item.get('collected_dynamic_variables') or item.get('metadata') or {},
            'provider_payload': item,
        }
    else:
        # Legacy conversation-style payload
        started = parse_iso(item.get('start_time') or item.get('started_at'))
        ended = parse_iso(item.get('end_time') or item.get('ended_at'))
        duration = None
        if started and ended:
            try:
                duration = int((ended - started).total_seconds())
            except Exception:
                duration = 0
        summary = item.get('summary') if isinstance(item.get('summary'), dict) else {}
        defaults = {
            'user': None,
            'channel': Channel.WEB,
            'direction': Direction.OUTBOUND,
            'status': CommStatus.COMPLETED if ended else CommStatus.ONGOING,
            'provider': 'retell',
            'retell_conversation_id': conv_id,
            'started_at': started or datetime.now(dt_timezone.utc),
            'ended_at': ended,
            'duration_sec': (duration or 0),
            'message_count': item.get('message_count') or 0,
            'intent': summary.get('intent'),
            'transcript_excerpt': summary.get('overall'),
            'from_identity': item.get('from') or item.get('customer_number'),
            'to_identity': item.get('to') or item.get('agent_number'),
            'metadata': item.get('metadata') or {},
            'provider_payload': item,
        }
    # Simple heuristic de tokens (si API no provee usage todavía): contar palabras del extracto
    try:
        if defaults.get('transcript_excerpt') and not defaults.get('tokens_prompt'):
            approx_tokens = max(1, len((defaults['transcript_excerpt'] or '').split()))
            defaults['tokens_prompt'] = approx_tokens
    except Exception:
        pass
    obj, created = CommSession.objects.get_or_create(retell_conversation_id=conv_id, defaults=defaults)
    if not created:
        for f in ('status','ended_at','duration_sec','message_count','intent','transcript_excerpt','metadata'):
            if f in defaults:
                val = defaults.get(f)
                if val is not None and val != '':
                    setattr(obj, f, val)
        # Backfill de tokens si aún están en cero y ya tenemos transcript
        try:
            if (not getattr(obj, 'tokens_prompt', 0)) and (obj.transcript_excerpt):
                obj.tokens_prompt = max(1, len(obj.transcript_excerpt.split()))
        except Exception:
            pass
        obj.save()
    return obj, created


def _ingest_call_session(item: dict):
    """Create or update a CommSession for a voice call item from Retell."""
    if not isinstance(item, dict):
        return None, False
    from .models import CommSession, Channel, Direction, CommStatus
    def parse_ms(ms):
        if ms is None:
            return None
        try:
            return datetime.fromtimestamp(int(ms)/1000.0, tz=dt_timezone.utc)
        except Exception:
            return None
    def parse_iso(s):
        if not s:
            return None
        try:
            if isinstance(s, (int,float)):
                return datetime.fromtimestamp(float(s)/1000.0, tz=dt_timezone.utc)
            if isinstance(s, str) and s.endswith('Z'):
                s = s[:-1] + '+00:00'
            return datetime.fromisoformat(s)
        except Exception:
            return None
    call_id = item.get('call_id') or item.get('id')
    if not call_id:
        return None, False
    started = parse_ms(item.get('start_timestamp')) or parse_iso(item.get('start_time') or item.get('registered_time'))
    ended = parse_ms(item.get('end_timestamp')) or parse_iso(item.get('end_time'))
    dms = item.get('duration_ms')
    duration = None
    if isinstance(dms, (int,float)):
        duration = int(float(dms)/1000.0)
    elif started and ended:
        duration = int((ended - started).total_seconds())
    dir_raw = (item.get('direction') or '').lower()
    from_val = item.get('from') or item.get('customer_number')
    to_val = item.get('to') or item.get('agent_number')
    direction = Direction.INBOUND if dir_raw in ('inbound','incoming') else Direction.OUTBOUND
    transcript_text = (item.get('call_analysis') or {}).get('call_summary') or item.get('transcript') or None
    defaults = {
        'user': None,
        'channel': Channel.VOICE,
        'direction': direction,
        'status': CommStatus.COMPLETED if ended else CommStatus.ONGOING,
        'provider': 'retell',
        'retell_call_id': call_id,
        'started_at': started or datetime.now(dt_timezone.utc),
        'ended_at': ended,
        'duration_sec': duration or 0,
        'message_count': item.get('message_count') or 0,
        'intent': None,
        'transcript_excerpt': transcript_text[:180] if transcript_text else None,
        'from_identity': from_val,
        'to_identity': to_val,
        'metadata': item.get('metadata') or {},
        'provider_payload': item,
    }
    # Heurística igual para llamadas (usa transcript_excerpt)
    try:
        if defaults.get('transcript_excerpt') and not defaults.get('tokens_prompt'):
            defaults['tokens_prompt'] = max(1, len((defaults['transcript_excerpt'] or '').split()))
    except Exception:
        pass
    obj, created = CommSession.objects.get_or_create(retell_call_id=call_id, defaults=defaults)
    if not created:
        for f in ('status','ended_at','duration_sec','message_count','transcript_excerpt','metadata'):
            val = defaults.get(f)
            if val:
                setattr(obj, f, val)
        try:
            if (not getattr(obj, 'tokens_prompt', 0)) and obj.transcript_excerpt:
                obj.tokens_prompt = max(1, len(obj.transcript_excerpt.split()))
        except Exception:
            pass
        obj.save()
    return obj, created


class RetellWebhookView(APIView):
    """Signed webhook that now writes directly to CommSession (no Conversation intermediate)."""
    authentication_classes = []
    permission_classes = []

    EVENT_TYPE_MAP = {
        'call.completed': 'call',
        'chat.completed': 'chat',
    }

    def post(self, request):
        from .models import WebhookEvent, Channel

        raw_body = request.body
        secret = getattr(settings, 'RETELL_WEBHOOK_SECRET', None)
        if secret:
            sig = request.headers.get('X-Signature') or request.headers.get('X-Retell-Signature')
            if not sig:
                return Response({'error': 'missing signature'}, status=400)
            mac = hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(mac, sig):
                return Response({'error': 'invalid signature'}, status=401)

        try:
            payload = request.data if isinstance(request.data, dict) else jsonlib.loads(raw_body.decode('utf-8') or '{}')
        except Exception:
            payload = {}

        event_id = payload.get('event_id') or payload.get('id') or payload.get('eventId')
        if event_id:
            we, created = WebhookEvent.objects.get_or_create(event_id=event_id, defaults={'payload': payload})
            if not created:
                return Response({'status': 'ok', 'idempotent': True})

        ev_type = payload.get('type') or ''
        conv_type = self.EVENT_TYPE_MAP.get(ev_type)
        if not conv_type:
            conv_type = 'call' if payload.get('recording_url') or payload.get('call_id') else 'chat'

        # Choose ingestion helper
        root = payload.get('conversation') if isinstance(payload.get('conversation'), dict) else payload
        session = None
        created_flag = False
        if conv_type == 'call':
            session, created_flag = _ingest_call_session(root)
        else:
            session, created_flag = _ingest_chat_session(root)
        # Light background refresh to reconcile list endpoints
        try:
            refresh_retell_sessions(lite=True)
        except Exception:
            pass
        if not session:
            return Response({'error': 'unable to ingest'}, status=400)

        # Ingest messages if present
        helper = RetellSyncWebhookView()
        msgs = helper._extract_messages(root)
        if msgs:
            stats = {'messages_created': 0, 'messages_updated': 0, 'attachments_created': 0}
            chan = Channel.VOICE if conv_type == 'call' else Channel.WEB
            for m in msgs:
                helper._ensure_message(session, chan, m, stats)
            session.message_count = session.messages.count()
            session.save(update_fields=['message_count', 'updated_at'])
        else:
            # If only transcript/summary
            transcript = root.get('transcript') or (root.get('summary') or {}).get('overall')
            if transcript:
                stats = {'messages_created': 0, 'messages_updated': 0, 'attachments_created': 0}
                chan = Channel.VOICE if conv_type == 'call' else Channel.WEB
                helper._ensure_message(session, chan, {
                    'id': f"{session.retell_call_id or session.retell_conversation_id}_summary",
                    'role': 'assistant',
                    'content': transcript,
                    'timestamp': (session.ended_at or session.started_at).isoformat() if (session.ended_at or session.started_at) else None,
                }, stats)
                session.message_count = session.messages.count()
                session.save(update_fields=['message_count', 'updated_at'])

        return Response({'status': 'ok', 'created': created_flag})


def refresh_retell_sessions(lite: bool=False):
    """Fetch chats from list-chat and calls from v2/list-calls only; upsert CommSession.
    lite=True omite diagnósticos detallados.
    """
    from .models import CommSession
    api_key = getattr(settings, 'RETELL_API_KEY', '')
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    # Correct chat endpoints: prefer POST /list-chats (object with "chats"), fallback GET /list-chat (array)
    chat_post_url = 'https://api.retellai.com/list-chats'
    chat_get_url = 'https://api.retellai.com/list-chat'
    calls_url = 'https://api.retellai.com/v2/list-calls'
    created_chat = updated_chat = created_call = updated_call = 0
    diag = {} if not lite else None
    # Chats
    try:
        items = []
        # Primary: POST /list-chats
        rc = requests.post(chat_post_url, headers=headers, json={'limit': 1000}, timeout=25)
        if rc.ok:
            data = rc.json() or {}
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                items = data.get('chats') or data.get('data') or data.get('items') or []
        else:
            if diag is not None: diag['chat_post_status'] = rc.status_code
        # Fallback: GET /list-chat
        if not items:
            rg = requests.get(chat_get_url, headers={'Authorization': headers['Authorization'], 'Accept': 'application/json'}, params={'limit': 1000}, timeout=25)
            if rg.ok:
                gdata = rg.json() if rg.headers.get('Content-Type','').startswith('application/json') else []
                if isinstance(gdata, list):
                    items = gdata
                elif isinstance(gdata, dict):
                    items = gdata.get('chats') or gdata.get('data') or gdata.get('items') or []
            else:
                if diag is not None: diag['chat_get_status'] = rg.status_code
        for it in items:
            cid = it.get('conversation_id') or it.get('id') or it.get('chat_id')
            if not cid:
                continue
            existed = CommSession.objects.filter(retell_conversation_id=cid).exists()
            _ingest_chat_session(it)
            if existed: updated_chat += 1
            else: created_chat += 1
        if diag is not None:
            diag['chat_count'] = len(items)
    except Exception as e:
        if diag is not None: diag['chat_error'] = str(e)
    # Calls
    try:
        rc2 = requests.post(calls_url, headers=headers, json={'limit': 1000}, timeout=25)
        if rc2.ok:
            data2 = rc2.json() or {}
            items2 = data2.get('calls') or data2.get('data') or data2.get('items') or []
            for it in items2:
                call_id = it.get('call_id') or it.get('id')
                if not call_id:
                    continue
                existed = CommSession.objects.filter(retell_call_id=call_id).exists()
                _ingest_call_session(it)
                if existed: updated_call += 1
                else: created_call += 1
            if diag is not None: diag['calls_count'] = len(items2)
        else:
            if diag is not None: diag['calls_status'] = rc2.status_code
    except Exception as e:
        if diag is not None: diag['calls_error'] = str(e)
    return {
        'chat': {'created': created_chat, 'updated': updated_chat},
        'call': {'created': created_call, 'updated': updated_call},
        'totals': {'created': created_chat + created_call, 'updated': updated_chat + updated_call},
        **({'diag': diag} if diag is not None else {})
    }


class MyConversationsListView(APIView):
    """Backward-compatible endpoint now sourcing from CommSession (web + voice)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .models import CommSession, Channel
        qs = CommSession.objects.filter(user=request.user).order_by('-ended_at')
        ctype = request.query_params.get('type')
        if ctype == 'chat':
            qs = qs.filter(channel=Channel.WEB)
        elif ctype == 'call':
            qs = qs.filter(channel=Channel.VOICE)
        started_after = request.query_params.get('started_after')
        ended_before = request.query_params.get('ended_before')
        from datetime import datetime
        def parse_iso(s):
            if not s:
                return None
            try:
                if isinstance(s, str) and s.endswith('Z'):
                    s = s[:-1] + '+00:00'
                return datetime.fromisoformat(s)
            except Exception:
                return None
        if started_after:
            dt = parse_iso(started_after)
            if dt:
                qs = qs.filter(started_at__gte=dt)
        if ended_before:
            dt = parse_iso(ended_before)
            if dt:
                qs = qs.filter(ended_at__lte=dt)

        # Simple pagination
        page = int(request.query_params.get('page', '1') or '1')
        page_size = min(max(int(request.query_params.get('page_size', '20') or '20'), 1), 100)
        total = qs.count()
        start = (page - 1) * page_size
        items = list(qs.values('conversation_id','type','started_at','ended_at','duration_seconds','transcript','recording_url','metadata')[start:start+page_size])
        return Response({
            'count': total,
            'page': page,
            'page_size': page_size,
            'results': items,
        })


class CommSessionDetailApiView(APIView):
    """Authenticated JSON detail for a communication session with messages."""
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            s = CommSession.objects.select_related().get(pk=pk)
        except CommSession.DoesNotExist:
            return Response({'error': 'not found'}, status=404)
        # Enforce ownership unless superuser
        if not request.user.is_superuser:
            if s.user_id and s.user_id != request.user.id:
                return Response({'error': 'forbidden'}, status=403)
        # Build payload
        data = {
            'id': s.id,
            'channel': s.channel,
            'direction': s.direction,
            'status': s.status,
            'started_at': s.started_at.isoformat() if s.started_at else None,
            'ended_at': s.ended_at.isoformat() if s.ended_at else None,
            'duration_sec': s.duration_sec,
            'message_count': s.message_count,
            'intent': s.intent,
            'transcript_excerpt': s.transcript_excerpt,
            'from_identity': s.from_identity,
            'to_identity': s.to_identity,
            'retell_call_id': s.retell_call_id,
            'retell_conversation_id': s.retell_conversation_id,
            'conversation_flow_id': s.conversation_flow_id,
            'metadata': s.metadata or {},
        }
        # Messages ordered by timestamp asc
        msgs = []
        existing_qs = s.messages.all().order_by('timestamp','id')
        for m in existing_qs:
            msgs.append({
                'id': m.id,
                'role': m.role,
                'content': m.content or '',
                'timestamp': m.timestamp.isoformat() if m.timestamp else None,
            })
        # Auto-hydrate chat messages on demand if web session has none yet
        if s.channel == Channel.WEB and not msgs:
            try:
                api_key = getattr(settings, 'RETELL_API_KEY', None)
                if api_key and (s.retell_conversation_id or s.provider_payload.get('chat_id')):
                    chat_id = s.retell_conversation_id or s.provider_payload.get('chat_id')
                    # get-chat/{chat_id}
                    detail_url = f"https://api.retellai.com/get-chat/{chat_id}"
                    r = requests.get(detail_url, headers={'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}, timeout=20)
                    if r.ok:
                        detail = r.json()
                        transcript = detail.get('transcript') or ''
                        # If transcript contains lines prefixed with 'Agent:' / 'User:' transform into messages
                        if transcript:
                            lines = [ln for ln in transcript.split('\n') if ln.strip()]
                            built = []
                            from .models import CommMessage, MessageRole
                            now = datetime.now(dt_timezone.utc)
                            for idx, ln in enumerate(lines):
                                role = None
                                text = ln
                                lower = ln.lower()
                                if lower.startswith('agent:'):
                                    role = MessageRole.ASSISTANT
                                    text = ln.split(':',1)[1].strip()
                                elif lower.startswith('user:'):
                                    role = MessageRole.USER
                                    text = ln.split(':',1)[1].strip()
                                if not role:
                                    # Try to infer alternating
                                    role = MessageRole.USER if (idx % 2 == 0) else MessageRole.ASSISTANT
                                msg_obj = CommMessage.objects.create(
                                    session=s,
                                    tenant=s.tenant,
                                    timestamp=now + timedelta(milliseconds=idx*10),
                                    channel=Channel.WEB,
                                    role=role,
                                    content=text[:4000],
                                    metadata={'auto_built': True}
                                )
                                built.append(msg_obj)
                            # refresh list
                            s.message_count = s.messages.count()
                            s.save(update_fields=['message_count','updated_at'])
                            msgs = [{
                                'id': m.id,
                                'role': m.role,
                                'content': m.content or '',
                                'timestamp': m.timestamp.isoformat() if m.timestamp else None,
                            } for m in built]
                        # If API returns structured messages later we can extend here
            except Exception:
                pass
        data['messages'] = msgs
        return Response({'ok': True, 'session': data})
