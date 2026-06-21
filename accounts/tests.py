"""
Tests for the accounts app.

Covers models, forms, views, and authentication flows including:
    - User and profile model creation
    - Registration with validation
    - Email verification token generation and checking
    - Login/logout flows
    - Password reset workflow
    - Profile creation and updates
    - Protected route access control
"""

from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.messages import get_messages
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.forms import (
    LoginForm,
    ProfileUpdateForm,
    RegistrationForm,
)
from accounts.models import CustomUser, UserProfile
from accounts.tokens import email_verification_token

User = get_user_model()


# ============================================================================
# Model Tests
# ============================================================================


class CustomUserModelTests(TestCase):
    """Test CustomUser model creation, string representation, and methods."""

    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'password': 'SecurePass123!',
        }

    def test_create_user_successfully(self):
        """A user can be created with valid email and password."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.first_name, 'John')
        self.assertEqual(user.last_name, 'Doe')
        self.assertTrue(user.check_password('SecurePass123!'))
        self.assertFalse(user.is_active)  # Default is False
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        """Creating a user without an email should raise ValueError."""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='pass123')

    def test_create_superuser_successfully(self):
        """A superuser can be created and has correct permissions."""
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPass123!',
        )
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)

    def test_create_superuser_must_have_is_staff(self):
        """Superuser creation must enforce is_staff=True."""
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='admin@example.com',
                password='pass123',
                is_staff=False,
            )

    def test_user_str_returns_email(self):
        """__str__ should return the email address."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')

    def test_get_full_name(self):
        """get_full_name should combine first and last name."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_full_name(), 'John Doe')

    def test_get_short_name(self):
        """get_short_name should return first name."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), 'John')

    def test_email_normalization(self):
        """Email should be normalized (lowercased domain)."""
        user = User.objects.create_user(
            email='Test@Example.COM',
            first_name='Test',
            last_name='User',
            password='pass123',
        )
        self.assertEqual(user.email, 'Test@example.com')

    def test_email_uniqueness(self):
        """Duplicate email addresses should be rejected."""
        User.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create_user(**self.user_data)


class UserProfileModelTests(TestCase):
    """Test UserProfile creation and relationships."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profile@example.com',
            first_name='Jane',
            last_name='Smith',
            password='SecurePass123!',
        )

    def test_profile_created_automatically(self):
        """A profile should be auto-created when a user is created."""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)

    def test_profile_str_representation(self):
        """Profile __str__ should contain the user's email."""
        self.assertIn('profile@example.com', str(self.user.profile))

    def test_profile_default_fields(self):
        """New profile should have default empty values."""
        profile = self.user.profile
        self.assertFalse(profile.avatar)  # No file attached
        self.assertEqual(profile.bio, '')
        self.assertIsNotNone(profile.created_at)
        self.assertIsNotNone(profile.updated_at)


# ============================================================================
# Token Tests
# ============================================================================


class EmailVerificationTokenTests(TestCase):
    """Test email verification token generation and validation."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='token@example.com',
            first_name='Token',
            last_name='Test',
            password='SecurePass123!',
        )

    def test_token_generation(self):
        """A valid token should be generated for a user."""
        token = email_verification_token.make_token(self.user)
        self.assertTrue(token)
        self.assertIsInstance(token, str)

    def test_token_validation_with_valid_token(self):
        """A generated token should be valid for the same user."""
        token = email_verification_token.make_token(self.user)
        self.assertTrue(
            email_verification_token.check_token(self.user, token)
        )

    def test_token_invalid_for_different_user(self):
        """A token should not be valid for a different user."""
        other_user = User.objects.create_user(
            email='other@example.com',
            first_name='Other',
            last_name='User',
            password='SecurePass123!',
        )
        token = email_verification_token.make_token(self.user)
        self.assertFalse(
            email_verification_token.check_token(other_user, token)
        )

    def test_token_invalid_after_activation(self):
        """A token should become invalid after the user is activated."""
        token = email_verification_token.make_token(self.user)
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])
        self.assertFalse(
            email_verification_token.check_token(self.user, token)
        )

    def test_token_with_fake_token(self):
        """A fake/malformed token should be rejected."""
        self.assertFalse(
            email_verification_token.check_token(self.user, 'fake-token-123')
        )


# ============================================================================
# Form Tests
# ============================================================================


class RegistrationFormTests(TestCase):
    """Test registration form validation."""

    def setUp(self):
        self.valid_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }

    def test_valid_registration_form(self):
        """Form should be valid with correct data."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Form should reject non-matching passwords."""
        data = self.valid_data.copy()
        data['confirm_password'] = 'DifferentPass456!'
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_password', form.errors)

    def test_duplicate_email(self):
        """Form should reject duplicate email addresses."""
        User.objects.create_user(
            email='newuser@example.com',
            first_name='Existing',
            last_name='User',
            password='ExistingPass123!',
        )
        form = RegistrationForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_weak_password(self):
        """Form should reject weak passwords."""
        data = self.valid_data.copy()
        data['password'] = '123'
        data['confirm_password'] = '123'
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_email_case_insensitive_uniqueness(self):
        """Email uniqueness should be case-insensitive."""
        User.objects.create_user(
            email='NewUser@Example.com',
            first_name='Existing',
            last_name='User',
            password='ExistingPass123!',
        )
        data = self.valid_data.copy()
        data['email'] = 'newuser@example.com'
        form = RegistrationForm(data=data)
        self.assertFalse(form.is_valid())

    def test_user_created_inactive(self):
        """User created via form should be inactive."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertFalse(user.is_active)

    def test_password_is_hashed(self):
        """Password should be hashed, not stored in plain text."""
        form = RegistrationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertNotEqual(user.password, 'StrongPass123!')
        self.assertTrue(
            user.password.startswith('pbkdf2_') or
            user.password.startswith('bcrypt') or
            user.password.startswith('argon2')
        )


class LoginFormTests(TestCase):
    """Test login form validation."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='login@example.com',
            first_name='Login',
            last_name='Test',
            password='SecurePass123!',
        )
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])

    def test_valid_login(self):
        """Form should be valid with correct credentials."""
        form = LoginForm(data={
            'email': 'login@example.com',
            'password': 'SecurePass123!',
        })
        self.assertTrue(form.is_valid())

    def test_invalid_password(self):
        """Form should reject wrong password."""
        form = LoginForm(data={
            'email': 'login@example.com',
            'password': 'WrongPassword!',
        })
        self.assertFalse(form.is_valid())

    def test_inactive_user_cannot_login(self):
        """Form should reject inactive users."""
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])
        form = LoginForm(data={
            'email': 'login@example.com',
            'password': 'SecurePass123!',
        })
        self.assertFalse(form.is_valid())

    def test_nonexistent_email(self):
        """Form should reject non-existent email."""
        form = LoginForm(data={
            'email': 'nonexistent@example.com',
            'password': 'SomePass123!',
        })
        self.assertFalse(form.is_valid())

    def test_email_case_insensitive(self):
        """Login should work with different email casing."""
        form = LoginForm(data={
            'email': 'LOGIN@EXAMPLE.COM',
            'password': 'SecurePass123!',
        })
        self.assertTrue(form.is_valid())


class ProfileUpdateFormTests(TestCase):
    """Test profile update form."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profileupdate@example.com',
            first_name='Profile',
            last_name='Update',
            password='SecurePass123!',
        )

    def test_valid_profile_update(self):
        """Form should be valid with correct data."""
        form = ProfileUpdateForm(
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'bio': 'This is my bio.',
            },
            user=self.user,
        )
        self.assertTrue(form.is_valid())

    def test_profile_update_saves_user_fields(self):
        """Form should update user's first and last name."""
        profile = self.user.profile
        form = ProfileUpdateForm(
            data={
                'first_name': 'Updated',
                'last_name': 'Name',
                'bio': 'New bio text.',
            },
            instance=profile,
            user=self.user,
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')


# ============================================================================
# View Tests
# ============================================================================


class RegistrationViewTests(TestCase):
    """Test the registration view and workflow."""

    def test_registration_page_loads(self):
        """Registration page should return 200."""
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/register.html')

    def test_successful_registration_sends_email(self):
        """Registration should send a verification email."""
        data = {
            'email': 'register@example.com',
            'first_name': 'Register',
            'last_name': 'Test',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        response = self.client.post(reverse('accounts:register'), data)
        self.assertRedirects(response, reverse('accounts:verify_email_sent'))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate Your Account', mail.outbox[0].subject)

    def test_registration_creates_inactive_user(self):
        """Registration should create an inactive user."""
        data = {
            'email': 'inactive@example.com',
            'first_name': 'Inactive',
            'last_name': 'User',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        }
        self.client.post(reverse('accounts:register'), data)
        user = User.objects.get(email='inactive@example.com')
        self.assertFalse(user.is_active)

    def test_registration_redirects_authenticated_user(self):
        """Authenticated users should be redirected away from register."""
        user = User.objects.create_user(
            email='auth@example.com',
            first_name='Auth',
            last_name='User',
            password='SecurePass123!',
        )
        user.is_active = True
        user.save()
        self.client.force_login(user)
        response = self.client.get(reverse('accounts:register'))
        self.assertRedirects(response, reverse('accounts:dashboard'))


class ActivationViewTests(TestCase):
    """Test email activation workflow."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='activate@example.com',
            first_name='Activate',
            last_name='Test',
            password='SecurePass123!',
        )
        self.token = email_verification_token.make_token(self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))

    def test_successful_activation(self):
        """Valid activation link should activate the user."""
        url = reverse('accounts:activate', args=[self.uid, self.token])
        response = self.client.get(url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
        self.assertTemplateUsed(response, 'accounts/verify_email_success.html')

    def test_activation_with_invalid_token(self):
        """Invalid token should show failure page."""
        url = reverse('accounts:activate', args=[self.uid, 'invalid-token'])
        response = self.client.get(url)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTemplateUsed(response, 'accounts/verify_email_failed.html')

    def test_activation_logs_user_in(self):
        """Successful activation should log the user in."""
        url = reverse('accounts:activate', args=[self.uid, self.token])
        self.client.get(url)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_already_active_user(self):
        """Already active users should be redirected."""
        self.user.is_active = True
        self.user.save()
        # Generate a new token after setting active so it validates
        new_token = email_verification_token.make_token(self.user)
        url = reverse('accounts:activate', args=[self.uid, new_token])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('accounts:login'))


class LoginViewTests(TestCase):
    """Test login view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='logintest@example.com',
            first_name='Login',
            last_name='Test',
            password='SecurePass123!',
        )
        self.user.is_active = True
        self.user.save(update_fields=['is_active'])

    def test_login_page_loads(self):
        """Login page should return 200."""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_successful_login(self):
        """Valid credentials should log the user in."""
        response = self.client.post(reverse('accounts:login'), {
            'email': 'logintest@example.com',
            'password': 'SecurePass123!',
        })
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_inactive_user_cannot_login(self):
        """Inactive users should see an error message."""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(reverse('accounts:login'), {
            'email': 'logintest@example.com',
            'password': 'SecurePass123!',
        })
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_authenticated_user_redirected(self):
        """Authenticated users should be redirected away from login."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:login'))
        self.assertRedirects(response, reverse('accounts:dashboard'))

    def test_remember_me_sets_session_expiry(self):
        """Remember me unchecked should set session to expire on close."""
        self.client.post(reverse('accounts:login'), {
            'email': 'logintest@example.com',
            'password': 'SecurePass123!',
        })
        # Session should expire on browser close since remember_me not set
        session = self.client.session
        self.assertTrue(session.get_expire_at_browser_close())


class LogoutViewTests(TestCase):
    """Test logout view."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='logout@example.com',
            first_name='Logout',
            last_name='Test',
            password='SecurePass123!',
        )
        self.user.is_active = True
        self.user.save()
        self.client.force_login(self.user)

    def test_logout_redirects_to_login(self):
        """Logout should redirect to login page."""
        response = self.client.post(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))

    def test_user_is_logged_out(self):
        """User should not be authenticated after logout."""
        self.client.post(reverse('accounts:logout'))
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}",
        )

    def test_logout_via_get(self):
        """GET request to logout should also work."""
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('accounts:login'))


class PasswordResetViewTests(TestCase):
    """Test password reset workflow."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='reset@example.com',
            first_name='Reset',
            last_name='Test',
            password='OldPass123!',
        )
        self.user.is_active = True
        self.user.save()

    def test_password_reset_page_loads(self):
        """Password reset page should return 200."""
        response = self.client.get(reverse('accounts:password_reset'))
        self.assertEqual(response.status_code, 200)

    def test_password_reset_sends_email(self):
        """Valid email should send a reset email."""
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'reset@example.com'},
        )
        self.assertRedirects(
            response,
            reverse('accounts:password_reset_done'),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Reset your', mail.outbox[0].subject)

    def test_password_reset_nonexistent_email(self):
        """Non-existent email should still redirect (security best practice)."""
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'nonexistent@example.com'},
        )
        self.assertRedirects(
            response,
            reverse('accounts:password_reset_done'),
        )
        self.assertEqual(len(mail.outbox), 0)


class ProtectedViewTests(TestCase):
    """Test that protected views require authentication."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='protected@example.com',
            first_name='Protected',
            last_name='Test',
            password='SecurePass123!',
        )
        self.user.is_active = True
        self.user.save()

    def test_dashboard_redirects_unauthenticated(self):
        """Unauthenticated users should be redirected from dashboard."""
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:dashboard')}",
        )

    def test_dashboard_accessible_when_authenticated(self):
        """Authenticated users should access dashboard."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/dashboard.html')

    def test_profile_redirects_unauthenticated(self):
        """Unauthenticated users should be redirected from profile."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:profile')}",
        )

    def test_profile_accessible_when_authenticated(self):
        """Authenticated users should access profile."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_account_settings_redirects_unauthenticated(self):
        """Unauthenticated users should be redirected from settings."""
        response = self.client.get(reverse('accounts:account_settings'))
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('accounts:account_settings')}",
        )

    def test_account_settings_accessible_when_authenticated(self):
        """Authenticated users should access settings."""
        self.client.force_login(self.user)
        response = self.client.get(reverse('accounts:account_settings'))
        self.assertEqual(response.status_code, 200)


class ProfileViewTests(TestCase):
    """Test profile view and updates."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='profileview@example.com',
            first_name='Profile',
            last_name='View',
            password='SecurePass123!',
        )
        self.user.is_active = True
        self.user.save()
        self.client.force_login(self.user)

    def test_profile_update_success(self):
        """Profile update should save changes."""
        response = self.client.post(
            reverse('accounts:profile'),
            {
                'first_name': 'Updated',
                'last_name': 'Name',
                'bio': 'Updated bio text.',
            },
        )
        self.assertRedirects(response, reverse('accounts:profile'))
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_profile_context_has_user(self):
        """Profile page should contain user information."""
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 200)


# ============================================================================
# Integration Tests
# ============================================================================


class FullRegistrationFlowTests(TestCase):
    """Test the complete registration-to-activation flow."""

    def test_full_registration_and_activation_flow(self):
        """Complete flow: register, get email, activate, login."""
        # Step 1: Register
        response = self.client.post(reverse('accounts:register'), {
            'email': 'fullflow@example.com',
            'first_name': 'Full',
            'last_name': 'Flow',
            'password': 'StrongPass123!',
            'confirm_password': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('accounts:verify_email_sent'))

        # Step 2: Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Activate Your Account', mail.outbox[0].subject)

        # Step 3: Extract activation link from email and follow it
        user = User.objects.get(email='fullflow@example.com')
        self.assertFalse(user.is_active)

        token = email_verification_token.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        activation_url = reverse('accounts:activate', args=[uid, token])
        response = self.client.get(activation_url)

        # Step 4: Verify user is now active
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTemplateUsed(response, 'accounts/verify_email_success.html')

        # Step 5: User should be logged in and can access dashboard
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(response.status_code, 200)


class PasswordResetFullFlowTests(TestCase):
    """Test the complete password reset flow."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='resetflow@example.com',
            first_name='Reset',
            last_name='Flow',
            password='OldPass123!',
        )
        self.user.is_active = True
        self.user.save()

    def test_full_password_reset_flow(self):
        """Complete flow: request reset, click link, set new password."""
        # Step 1: Request password reset
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'email': 'resetflow@example.com'},
        )
        self.assertRedirects(response, reverse('accounts:password_reset_done'))

        # Step 2: Extract reset link from email
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body

        # Find the reset URL in the email body
        import re
        match = re.search(r'/password-reset-confirm/([^/]+)/([^/]+)/', email_body)
        self.assertIsNotNone(match)
        uidb64, token = match.group(1), match.group(2)

        # Step 3: Access reset confirm page
        # Django's PasswordResetConfirmView redirects on valid token to
        # a session-based URL (to prevent token reuse on POST). Follow it.
        reset_url = reverse(
            'accounts:password_reset_confirm',
            args=[uidb64, token],
        )
        response = self.client.get(reset_url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Step 4: Set new password
        # Extract the final URL after redirects for the POST
        final_reset_url = response.redirect_chain[-1][0] if response.redirect_chain else reset_url
        response = self.client.post(
            final_reset_url,
            {
                'new_password1': 'NewStrongPass456!',
                'new_password2': 'NewStrongPass456!',
            },
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('accounts:password_reset_complete'),
        )

        # Step 5: Verify new password works
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewStrongPass456!'))


class SecurityTests(TestCase):
    """Test security-related functionality."""

    def test_csrf_protection_on_login(self):
        """Login form should include CSRF token."""
        response = self.client.get(reverse('accounts:login'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_csrf_protection_on_register(self):
        """Register form should include CSRF token."""
        response = self.client.get(reverse('accounts:register'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_password_hashing(self):
        """Passwords should be hashed with a strong algorithm."""
        user = User.objects.create_user(
            email='security@example.com',
            first_name='Security',
            last_name='Test',
            password='SecurePass123!',
        )
        self.assertNotEqual(user.password, 'SecurePass123!')
        self.assertTrue(
            user.password.startswith('pbkdf2_') or
            user.password.startswith('bcrypt') or
            user.password.startswith('argon2')
        )

    def test_session_security_on_logout(self):
        """Session should be invalidated on logout."""
        user = User.objects.create_user(
            email='session@example.com',
            first_name='Session',
            last_name='Test',
            password='SecurePass123!',
        )
        user.is_active = True
        user.save()
        self.client.force_login(user)

        # Log out
        self.client.post(reverse('accounts:logout'))

        # Try to access protected page (should redirect to login)
        response = self.client.get(reverse('accounts:dashboard'))
        self.assertNotEqual(response.status_code, 200)
