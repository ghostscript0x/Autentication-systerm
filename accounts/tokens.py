"""
Token generation for email verification.

Uses Django's PasswordResetTokenGenerator to create secure,
time-limited signed tokens for account activation links.
"""

from django.contrib.auth.tokens import PasswordResetTokenGenerator


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    Generates secure tokens for email verification.

    Extends Django's PasswordResetTokenGenerator to create
    signed tokens that expire after a configurable timeout.
    Tokens are tied to a specific user and can only be used
    once (the user's last_login changes after activation).
    """

    def _make_hash_value(self, user, timestamp: int) -> str:
        """
        Create a hash value unique to the user for token generation.

        Combines the user's primary key, the timestamp, and
        the user's is_active status. If the user becomes active
        (email verified), previously generated tokens become invalid.

        Args:
            user: The user model instance.
            timestamp: The current timestamp.

        Returns:
            str: A string used to generate the hash.
        """
        return str(user.pk) + str(timestamp) + str(user.is_active)


email_verification_token = EmailVerificationTokenGenerator()
