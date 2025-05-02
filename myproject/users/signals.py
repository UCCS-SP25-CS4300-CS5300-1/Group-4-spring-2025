"""
This file contains the signals for the users app.
"""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile

def user_created_callback(user):
    """
    Function that can be called when a user is created
    This is a separate function to make it testable
    """
    return f"User {user.username} was created successfully"

@receiver(post_save, sender=User)
def create_user_profile(instance, created, **kwargs): # pylint: disable=unused-argument
    """
    Signal handler to create a user profile when a user is created
    """
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_profile(instance, **kwargs): # pylint: disable=unused-argument
    """
    Signal handler to save a user profile when a user is saved
    """
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        Profile.objects.get_or_create(user=instance)
