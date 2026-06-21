"""
Forms for the accounts app.

Provides form classes for user registration, login, profile updates,
and password-related operations. All forms include proper validation,
error handling, and accessibility attributes.
"""

from django import forms
from django.contrib.auth import authenticate, password_validation
from django.contrib.auth.forms import (
    PasswordResetForm,
    SetPasswordForm,
)
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from accounts.models import CustomUser, UserProfile


# Shared input class for Tailwind-styled form fields
_INPUT_CLASS = (
    'auth-input w-full bg-white/5 border border-white/10 rounded-xl px-10 py-2.5 '
    'text-sm text-white placeholder-slate-500 '
    'transition-all duration-200 '
    'focus:bg-white/[0.07] focus:border-indigo-500/50 '
    'hover:bg-white/10'
)

_INPUT_CLASS_NO_ICON = (
    'auth-input w-full bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 '
    'text-sm text-white placeholder-slate-500 '
    'transition-all duration-200 '
    'focus:bg-white/[0.07] focus:border-indigo-500/50 '
    'hover:bg-white/10'
)


class RegistrationForm(forms.ModelForm):
    """
    Form for new user registration.

    Collects email, first name, last name, and password.
    Validates password strength and confirmation.
    Creates the user with is_active=False (requires email verification).
    """

    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Enter your password',
            'autocomplete': 'new-password',
            'data-pw-toggle': 'true',
        }),
        help_text=password_validation.password_validators_help_text_html(),
    )
    confirm_password = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS,
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
            'data-pw-toggle': 'true',
        }),
    )

    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': _INPUT_CLASS + ' pl-10',
                'placeholder': 'Enter your email',
                'autocomplete': 'email',
            }),
            'first_name': forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'Enter your first name',
                'autocomplete': 'given-name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': _INPUT_CLASS,
                'placeholder': 'Enter your last name',
                'autocomplete': 'family-name',
            }),
        }

    def clean_email(self) -> str:
        """Validate that the email is unique (case-insensitive)."""
        email = self.cleaned_data.get('email', '').lower().strip()
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                _('A user with this email address already exists.'),
                code='duplicate_email',
            )
        return email

    def clean_password(self) -> str:
        """Validate password strength using Django's validators."""
        password = self.cleaned_data.get('password', '')
        password_validation.validate_password(password)
        return password

    def clean_confirm_password(self) -> str:
        """Validate that passwords match."""
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password', '')

        if password and confirm_password and password != confirm_password:
            raise ValidationError(
                _('Passwords do not match.'),
                code='password_mismatch',
            )
        return confirm_password

    def save(self, commit: bool = True) -> CustomUser:
        """
        Create the user with hashed password and is_active=False.

        Args:
            commit: If True, save to database immediately.

        Returns:
            CustomUser: The created user instance.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.is_active = False
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """
    Form for user authentication.

    Authenticates using email and password. Supports a
    'remember me' option for session persistence.
    """

    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': _INPUT_CLASS + ' pl-10',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
            'autofocus': True,
        }),
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS + ' pl-10',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'data-pw-toggle': 'true',
        }),
    )
    remember_me = forms.BooleanField(
        label=_('Remember Me'),
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'w-4 h-4 rounded bg-white/5 border border-white/10 text-indigo-600 focus:ring-indigo-500/50 focus:ring-offset-0 cursor-pointer',
        }),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self) -> dict:
        """
        Validate credentials and authenticate the user.

        Checks that the user exists, is active, and the password is correct.
        Inactive/unverified users are prevented from logging in.

        Returns:
            dict: The cleaned data.

        Raises:
            ValidationError: If credentials are invalid or account is inactive.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get('email', '').lower().strip()
        password = cleaned_data.get('password', '')

        if email and password:
            try:
                user = CustomUser.objects.get(email__iexact=email)
                if not user.is_active:
                    raise ValidationError(
                        _(
                            'Your account is not activated. '
                            'Please check your email for the activation link.'
                        ),
                        code='inactive_account',
                    )
            except CustomUser.DoesNotExist:
                raise ValidationError(
                    _('Invalid email or password.'),
                    code='invalid_login',
                )

            self.user_cache = authenticate(
                request=self.request,
                email=email,
                password=password,
            )
            if self.user_cache is None:
                raise ValidationError(
                    _('Invalid email or password.'),
                    code='invalid_login',
                )

        return cleaned_data

    def get_user(self):
        """Return the authenticated user."""
        return self.user_cache


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for users to update their profile information.

    Allows editing of first name, last name, bio, and avatar.
    """

    class Meta:
        model = UserProfile
        fields = ['avatar', 'bio']
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': _INPUT_CLASS_NO_ICON + ' file:mr-4 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-white/10 file:bg-white/5 file:text-slate-300 file:text-xs file:cursor-pointer hover:file:bg-white/10 file:transition-all',
                'accept': 'image/*',
            }),
            'bio': forms.Textarea(attrs={
                'class': _INPUT_CLASS_NO_ICON + ' resize-none',
                'rows': 4,
                'placeholder': 'Tell us about yourself...',
            }),
        }

    first_name = forms.CharField(
        label=_('First Name'),
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS_NO_ICON,
            'autocomplete': 'given-name',
        }),
    )
    last_name = forms.CharField(
        label=_('Last Name'),
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': _INPUT_CLASS_NO_ICON,
            'autocomplete': 'family-name',
        }),
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.user:
            self.fields['first_name'].initial = self.user.first_name
            self.fields['last_name'].initial = self.user.last_name

    def save(self, commit: bool = True) -> UserProfile:
        """
        Save the profile and update the user's name fields.

        Args:
            commit: If True, save to database immediately.

        Returns:
            UserProfile: The updated profile instance.
        """
        profile = super().save(commit=False)
        if self.user:
            self.user.first_name = self.cleaned_data['first_name']
            self.user.last_name = self.cleaned_data['last_name']
            if commit:
                self.user.save()
                profile.save()
        return profile


class CustomPasswordResetForm(PasswordResetForm):
    """
    Custom password reset form with Tailwind styling.

    Extends Django's built-in PasswordResetForm for consistent
    styling and additional validation.
    """

    email = forms.EmailField(
        label=_('Email'),
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': _INPUT_CLASS + ' pl-10',
            'placeholder': 'Enter your registered email',
            'autocomplete': 'email',
            'autofocus': True,
        }),
    )


class CustomSetPasswordForm(SetPasswordForm):
    """
    Custom set password form with Tailwind styling.

    Extends Django's built-in SetPasswordForm for consistent
    styling during password reset confirmation.
    """

    new_password1 = forms.CharField(
        label=_('New Password'),
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS + ' pl-10',
            'placeholder': 'Enter your new password',
            'autocomplete': 'new-password',
            'data-pw-toggle': 'true',
        }),
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_('Confirm New Password'),
        widget=forms.PasswordInput(attrs={
            'class': _INPUT_CLASS + ' pl-10',
            'placeholder': 'Confirm your new password',
            'autocomplete': 'new-password',
            'data-pw-toggle': 'true',
        }),
    )
