"""
Custom user manager for the authentication system.

Provides manager methods for creating regular users and superusers
with email as the unique identifier instead of username.
"""

from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    Custom manager for CustomUser model.

    Uses email as the unique identifier for authentication
    instead of the default username field.
    """

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """
        Create and save a regular user with the given email and password.

        Args:
            email: User's email address (used for authentication).
            password: User's password.
            extra_fields: Additional fields to set on the user model.

        Returns:
            CustomUser: The created user instance.

        Raises:
            ValueError: If email is not provided.
        """
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        """
        Create and save a superuser with the given email and password.

        Automatically sets is_staff=True, is_superuser=True, and is_active=True.

        Args:
            email: Superuser's email address.
            password: Superuser's password.
            extra_fields: Additional fields to set on the user model.

        Returns:
            CustomUser: The created superuser instance.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)
