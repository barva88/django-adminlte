from django.shortcuts import redirect
from django.urls import reverse


class AdminDashboardLoginRequiredMiddleware:
    """Require login for any view coming from admin_adminlte.views.

    This middleware checks the view function module. If it starts with
    'admin_adminlte.views' and the user is not authenticated it redirects
    to the account login page. It allows access to /accounts, /admin,
    /static and /media paths so login/logout and static assets remain
    accessible.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # view_func may be a function or a class-based view (callable)
        module = getattr(view_func, '__module__', '')
        if not module:
            # class-based views appear as <class>.as_view().__wrapped__ -> module may vary
            func = getattr(view_func, '__wrapped__', None)
            module = getattr(func, '__module__', '') if func else ''

        if module.startswith('admin_adminlte.views'):
            # Allow access to static/media and auth endpoints
            path = request.path
            if path.startswith('/accounts') or path.startswith('/admin') or path.startswith('/static') or path.startswith('/media'):
                return None

            if not getattr(request, 'user', None) or not request.user.is_authenticated:
                return redirect(reverse('account_login'))

        return None
