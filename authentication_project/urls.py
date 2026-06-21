"""
Project-level URL configuration.

Maps the root URL to the accounts app and Django admin.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path


def root_redirect(request):
    """Redirect root URL to dashboard or login."""
    return redirect('accounts:dashboard')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),

    # Redirect root to dashboard (or login if not authenticated)
    path('', root_redirect, name='root'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )
