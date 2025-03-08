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
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to perform actions when a user is created or updated
    """
    ## TODO: need to implement some sort of profile idfk

    ## Update: Commented out user_created_callback function call
    # replaced with Profile.objects.create function call
    # Runs every time a user is created
    # User is the sender and therefore sends notification

    if created:
        # user_created_callback(instance)
        Profile.objects.create(user=instance)



@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

