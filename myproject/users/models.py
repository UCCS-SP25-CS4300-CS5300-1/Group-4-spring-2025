from django.db import models
from django.contrib.auth.models import User

def get_user_by_email(email):
    """
    Helper function to get a user by email
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None
