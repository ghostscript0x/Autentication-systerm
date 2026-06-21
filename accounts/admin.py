"""
Admin configuration for the accounts app.

Registers CustomUser and UserProfile models with the Django admin
interface, providing custom list displays and search capabilities.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, UserProfile


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Admin configuration for CustomUser.

    Configures list display, search fields, and form layouts
    for managing users in the Django admin interface.
    """

    list_display = [
        'email',
        'first_name',
        'last_name',
        'is_active',
        'is_staff',
        'date_joined',
    ]
    list_filter = ['is_active', 'is_staff', 'is_superuser']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            _('Personal Info'),
            {'fields': ('first_name', 'last_name')},
        ),
        (
            _('Permissions'),
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (
            _('Important Dates'),
            {'fields': ('last_login', 'date_joined')},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'email',
                    'first_name',
                    'last_name',
                    'password1',
                    'password2',
                ),
            },
        ),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile.

    Allows admins to view and manage user profiles.
    """

    list_display = ['user', 'created_at', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
