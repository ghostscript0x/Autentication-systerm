"""
Views for the accounts app.

Provides view functions and class-based views for:
    - Registration with email verification
    - Login/logout with session management
    - Email account activation
    - Password reset flow
    - User profile management
    - Protected dashboard and settings pages
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
    PasswordResetDoneView,
    PasswordResetView,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.views import View
from django.views.generic import TemplateView, UpdateView

import logging

from accounts.forms import (
    CustomPasswordResetForm,
    CustomSetPasswordForm,
    LoginForm,
    ProfileUpdateForm,
    RegistrationForm,
)
from accounts.models import CustomUser, UserProfile
from accounts.services import send_verification_email
from accounts.tokens import email_verification_token

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class RegisterView(View):
    """
    Handle user registration.

    GET  → Display registration form.
    POST → Validate form, create inactive user, send verification email.
    """

    template_name = 'accounts/register.html'

    def get(self, request: HttpRequest) -> HttpResponse:
        """Display the registration form."""
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = RegistrationForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request: HttpRequest) -> HttpResponse:
        """Process registration, send verification email."""
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            send_verification_email(request, user)
            messages.success(
                request,
                (
                    'Account created successfully! '
                    'Please check your email to verify your account.'
                ),
            )
            return redirect('accounts:verify_email_sent')
        return render(request, self.template_name, {'form': form})


# ---------------------------------------------------------------------------
# Email Verification
# ---------------------------------------------------------------------------


def verify_email_sent(request: HttpRequest) -> HttpResponse:
    """Display a page confirming the verification email was sent."""
    return render(request, 'accounts/verify_email_sent.html')


class ActivateAccountView(View):
    """
    Handle email verification via signed activation link.

    Validates the token from the URL, activates the user account,
    and logs the user in on success.
    """

    template_name_success = 'accounts/verify_email_success.html'
    template_name_failed = 'accounts/verify_email_failed.html'

    def get(self, request: HttpRequest, uidb64: str, token: str) -> HttpResponse:
        """
        Process the activation link.

        Decodes the user ID, checks the token validity,
        and activates the account if valid.

        Args:
            uidb64: Base64-encoded user primary key.
            token: Signed token for verification.
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        if user is not None and email_verification_token.check_token(user, token):
            if user.is_active:
                messages.info(request, 'Your account is already verified.')
                return redirect('accounts:login')

            user.is_active = True
            user.save(update_fields=['is_active'])
            login(request, user)
            messages.success(request, 'Your email has been verified! Welcome.')
            return render(request, self.template_name_success)
        else:
            return render(request, self.template_name_failed, {
                'invalid_token': True,
            })


# ---------------------------------------------------------------------------
# Login / Logout
# ---------------------------------------------------------------------------


class CustomLoginView(LoginView):
    """
    Custom login view with email-based authentication.

    Extends Django's built-in LoginView with:
        - Custom form with validation
        - Remember-me support
        - Redirect for already-authenticated users
    """

    form_class = LoginForm
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        """Handle remember-me checkbox for session expiry."""
        remember_me = form.cleaned_data.get('remember_me', False)
        if not remember_me:
            self.request.session.set_expiry(0)  # Session expires on browser close
        return super().form_valid(form)


class CustomLogoutView(View):
    """
    Handle secure logout.

    Flushes the session and redirects to the login page.
    """

    def post(self, request: HttpRequest) -> HttpResponse:
        """Log out the user and redirect to login."""
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('accounts:login')

    def get(self, request: HttpRequest) -> HttpResponse:
        """Handle GET requests by logging out as well."""
        return self.post(request)


# ---------------------------------------------------------------------------
# Password Reset
# ---------------------------------------------------------------------------


class CustomPasswordResetView(SuccessMessageMixin, PasswordResetView):
    """
    Handle password reset requests.

    Users enter their email, and a reset link is sent if the email exists.
    Catches email delivery failures gracefully — always shows the success
    page to avoid leaking whether an account exists.
    """

    form_class = CustomPasswordResetForm
    template_name = 'accounts/password_reset.html'
    success_url = reverse_lazy('accounts:password_reset_done')
    email_template_name = 'accounts/emails/password_reset_email.txt'
    html_email_template_name = 'accounts/emails/password_reset_email.html'
    subject_template_name = 'accounts/emails/password_reset_subject.txt'
    success_message = (
        'If an account exists with that email, '
        'a password reset link has been sent.'
    )

    def form_valid(self, form):
        """
        Try sending the password reset email.

        If SMTP fails (timeout, auth error, etc.), log the error and
        still show the success page — never reveal whether an email
        was actually sent or the account exists.
        """
        try:
            return super().form_valid(form)
        except Exception:
            logger.exception(
                'Password reset email failed to send — '
                'SMTP server may be unreachable.'
            )
            messages.success(self.request, self.success_message)
            return redirect(self.success_url)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Display a confirmation page after the reset email is sent."""
    template_name = 'accounts/password_reset_sent.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """
    Handle the password reset confirmation.

    Users with a valid token can set a new password.
    """

    form_class = CustomSetPasswordForm
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Display a success page after password is reset."""
    template_name = 'accounts/password_reset_complete.html'


# ---------------------------------------------------------------------------
# User Profile
# ---------------------------------------------------------------------------


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    Display and update the user's profile.

    Authenticated users can view and edit their profile information,
    including avatar, bio, first name, and last name.
    """

    model = UserProfile
    form_class = ProfileUpdateForm
    template_name = 'accounts/profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        """Return the profile for the currently logged-in user."""
        return self.request.user.profile

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Save profile changes and show success message."""
        messages.success(self.request, 'Your profile has been updated.')
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# Protected Pages
# ---------------------------------------------------------------------------


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Display the user's dashboard.

    A protected page showing user information and quick links.
    Only accessible to authenticated users.
    """

    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['profile'] = self.request.user.profile
        return context


class AccountSettingsView(LoginRequiredMixin, TemplateView):
    """
    Display a placeholder account settings page.

    A protected page for future account settings functionality.
    """

    template_name = 'accounts/account_settings.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        return context
