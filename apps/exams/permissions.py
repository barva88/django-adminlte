from rest_framework import permissions


class IsAuthenticatedAndSubscribed(permissions.BasePermission):
    """Allow access only to authenticated users with active subscription and credits."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        # Simple check - assumes Subscription relations exist
        sub = getattr(user, 'subscription', None)
        if not sub:
            # try to find via model if available
            try:
                from .models import Subscription
                sub = Subscription.objects.filter(user=user, status='active').first()
            except Exception:
                sub = None
        return bool(sub and sub.credits_remaining > 0)
