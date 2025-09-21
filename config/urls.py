"""core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.views.generic.base import RedirectView

# Use allauth class-based views but force them to render the project's
# existing AdminLTE templates under `templates/accounts/` so we don't
# introduce a new, different-looking template set.
from allauth.account import views as allauth_views

# Protect admin_adminlte views by decorating their callbacks with login_required
from django.contrib.auth.decorators import login_required
import admin_adminlte.urls as _admin_urls
from django.urls.resolvers import URLPattern, URLResolver
from apps.pages import views_profile as pages_profile_views


def _protect_patterns(patterns):
    # names or path segments to exclude from protection (auth endpoints)
    EXEMPT_NAMES = {
        'login', 'logout', 'register', 'password_reset', 'password_reset_done', 'password_reset_complete',
        'password_change', 'password_change_done', 'account_login', 'account_signup', 'account_reset_password'
    }
    for p in patterns:
        if isinstance(p, URLPattern):
            # skip patterns that are authentication endpoints by name or by substring
            name = getattr(p, 'name', None)
            if name in EXEMPT_NAMES or (name and any(k in name for k in ('password', 'account', 'login', 'logout', 'register'))):
                continue
            # decorate the view function
            p.callback = login_required(p.callback)
        elif isinstance(p, URLResolver):
            # avoid descending into included 'accounts' urlconfs
            if getattr(p, 'pattern', None) and 'accounts' in str(p.pattern):
                continue
            _protect_patterns(p.url_patterns)


# apply protection in-place
try:
    _protect_patterns(_admin_urls.urlpatterns)
except Exception:
    # if something goes wrong, fall back to unprotected include
    pass

urlpatterns = [
    # Admin dashboard (protected) should come before the generic pages
    # so the dashboard root is matched and enforces login_required.
    path('', include('admin_adminlte.urls')),
    path('', include('apps.pages.urls')),
    path('', include('apps.dyn_dt.urls')),
    path('', include('apps.dyn_api.urls')),
    path('charts/', include('apps.charts.urls')),
    path('api/communications/', include('apps.communications.urls')),
    path('faq/', include(('apps.faq.urls', 'faq'), namespace='faq')),
    path('soporte/', include(('apps.support.urls', 'support'), namespace='support')),
    path('subscriptions/', include(('apps.subscriptions.urls', 'subscriptions'), namespace='subscriptions')),
    path('exams/', include(('apps.exams.urls', 'apps.exams'), namespace='exams')),
    path("admin/", admin.site.urls),

    # Explicitly map key account views to the project's `templates/accounts/*` files
    path('accounts/login/', allauth_views.LoginView.as_view(template_name='accounts/login.html'), name='account_login'),
    path('accounts/signup/', allauth_views.SignupView.as_view(template_name='accounts/register.html'), name='account_signup'),
    path('accounts/password/reset/', allauth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='account_reset_password'),

    # Backwards-compatible route names some templates expect (e.g. 'login', 'logout', 'password_reset')
    path('login/', allauth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', allauth_views.LogoutView.as_view(), name='logout'),
    path('password-reset/', allauth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'), name='password_reset'),

    # Fallback to the full allauth URL set for the rest
    path('accounts/', include('allauth.urls')),
    # Project-level profile management (overwrite package example)
    path('profile/', pages_profile_views.profile_view, name='profile'),
    path('profile/edit/', pages_profile_views.profile_edit, name='profile_edit'),
    path('profile/delete/', pages_profile_views.profile_delete, name='profile_delete'),
    # Backwards-compatible redirects for alternate password-reset URL styles
    path('accounts/password-reset/done/', RedirectView.as_view(url='/accounts/password-reset-done/', permanent=False)),
    path('accounts/password-reset/complete/', RedirectView.as_view(url='/accounts/password-reset-complete/', permanent=False)),
    path('accounts/password/reset/done/', RedirectView.as_view(url='/accounts/password-reset-done/', permanent=False)),
    path('accounts/password/reset/complete/', RedirectView.as_view(url='/accounts/password-reset-complete/', permanent=False)),
    # Include the full admin_adminlte URL set. We applied `_protect_patterns` to
    # `admin_adminlte.urls` earlier so all those views are decorated with
    # `login_required` in-place and will redirect unauthenticated users to login.
    path('', include('admin_adminlte.urls')),
]
