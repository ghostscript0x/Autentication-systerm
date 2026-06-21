"""
Signal handlers for the accounts app.

Automatically creates a UserProfile whenever a new CustomUser is created.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import CustomUser, UserProfile


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance: CustomUser, created: bool, **kwargs):
    """
    Automatically create a UserProfile when a new CustomUser is created.

    This ensures every user has a profile without requiring
    explicit profile creation in views.

    Args:
        sender: The model class (CustomUser).
        instance: The actual user instance being saved.
        created: True if a new record was created.
        **kwargs: Additional keyword arguments.
    """
    if created:
        UserProfile.objects.create(user=instance)
