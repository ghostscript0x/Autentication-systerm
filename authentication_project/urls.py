"""
Project-level URL configuration.

Maps the root URL to the accounts app and Django admin.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    """Redirect root URL to dashboard or login."""
    return redirect('accounts:dashboard')


def favicon(request):
    """Return 204 No Content for favicon.ico requests.
    
    Browsers automatically request /favicon.ico. Without this,
    unauthenticated users would hit the login page redirect,
    and search engines/indexers see a 400/404 for every page.
    204 is the lightest valid response — no body, no redirect.
    """
    return HttpResponse(status=204)


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Lightweight favicon handler — prevents 400/404 on browser auto-request
    path('favicon.ico', favicon, name='favicon'),

    # Redirect root to dashboard (or login if not authenticated)
    path('', root_redirect, name='root'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
