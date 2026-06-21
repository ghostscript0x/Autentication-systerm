"""
Business logic and service layer for the accounts app.

Contains email sending logic and other domain operations
to keep views thin and focused on HTTP concerns.
"""

from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.tokens import email_verification_token


def send_verification_email(request, user) -> None:
    """
    Send an email verification link to the newly registered user.

    Generates a signed token, creates an activation URL, and sends
    an email with instructions to activate the account.

    Args:
        request: The HTTP request (used to build absolute URLs).
        user: The CustomUser instance to send the verification to.
    """
    token = email_verification_token.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    current_site = get_current_site(request)
    protocol = 'https' if request.is_secure() else 'http'

    activation_url = (
        f'{protocol}://{current_site.domain}'
        f'/accounts/activate/{uid}/{token}/'
    )

    subject = 'Activate Your Account'
    message = render_to_string('accounts/emails/activation_email.txt', {
        'user': user,
        'activation_url': activation_url,
        'site_name': current_site.name,
    })
    html_message = render_to_string('accounts/emails/activation_email.html', {
        'user': user,
        'activation_url': activation_url,
        'site_name': current_site.name,
    })

    send_mail(
        subject=subject,
        message=message,
        html_message=html_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )


def send_password_reset_email(request, user) -> None:
    """
    Send a password reset link to the user.

    Uses Django's built-in password reset system to generate
    the reset URL and sends it via email.

    Args:
        request: The HTTP request.
        user: The CustomUser instance requesting the reset.
    """
    from django.contrib.auth.forms import PasswordResetForm

    form = PasswordResetForm({'email': user.email})
    if form.is_valid():
        form.save(
            request=request,
            use_https=request.is_secure(),
            from_email=settings.DEFAULT_FROM_EMAIL,
            email_template_name='accounts/emails/password_reset_email.txt',
            html_email_template_name='accounts/emails/password_reset_email.html',
        )
