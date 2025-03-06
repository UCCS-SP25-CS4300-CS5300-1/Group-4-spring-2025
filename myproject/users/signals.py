from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

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

    if(created):
        user_created_callback(instance)
    pass 