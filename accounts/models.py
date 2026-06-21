"""
Custom user and profile models for the authentication system.

Defines:
    - CustomUser: Email-based user model replacing Django's default User.
    - UserProfile: One-to-one profile model with additional user information.
"""

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from accounts.managers import CustomUserManager


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model that uses email as the unique identifier.

    Replaces the default Django User model with email-based authentication.
    Users are created with is_active=False by default and must verify
    their email address before they can log in.

    Fields:
        email: Unique identifier for authentication.
        first_name: User's first name.
        last_name: User's last name.
        is_active: Whether the user's email has been verified.
        is_staff: Whether the user can access the admin site.
        date_joined: Timestamp of when the user registered.
    """

    email = models.EmailField(
        _('email address'),
        unique=True,
        max_length=255,
        help_text=_('Required. Used for authentication and notifications.'),
        error_messages={
            'unique': _('A user with this email address already exists.'),
        },
    )
    first_name = models.CharField(
        _('first name'),
        max_length=150,
        blank=False,
        help_text=_('Required.'),
    )
    last_name = models.CharField(
        _('last name'),
        max_length=150,
        blank=False,
        help_text=_('Required.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user can log in. '
            'Set to True after email verification.'
        ),
    )
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into the admin site.'),
    )
    date_joined = models.DateTimeField(
        _('date joined'),
        default=timezone.now,
    )

    objects = CustomUserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self) -> str:
        """Return string representation of the user."""
        return self.email

    def get_full_name(self) -> str:
        """Return the full name of the user."""
        return f'{self.first_name} {self.last_name}'.strip()

    def get_short_name(self) -> str:
        """Return the short name of the user."""
        return self.first_name


class UserProfile(models.Model):
    """
    Extended profile for a user.

    Provides additional user information beyond what is stored in
    the CustomUser model. Created automatically when a user is created.

    Fields:
        user: One-to-one relationship with CustomUser.
        avatar: Optional profile picture.
        bio: Short biography or description.
        created_at: Timestamp of when the profile was created.
        updated_at: Timestamp of the last profile update.
    """

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user'),
    )
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        blank=True,
        null=True,
        help_text=_('Optional profile picture.'),
    )
    bio = models.TextField(
        _('bio'),
        max_length=500,
        blank=True,
        help_text=_('A short description about yourself.'),
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
    )

    class Meta:
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')

    def __str__(self) -> str:
        """Return string representation of the profile."""
        return f'{self.user.email} - Profile'
