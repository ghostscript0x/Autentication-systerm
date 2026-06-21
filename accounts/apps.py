"""
App configuration for the accounts app.

Configures the accounts application and connects signal handlers.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration for the accounts application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        """Import signal handlers when the app is ready."""
        import accounts.signals  # noqa: F401 - Needed to register signals
