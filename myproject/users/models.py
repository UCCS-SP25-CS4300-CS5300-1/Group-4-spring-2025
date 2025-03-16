from django.db import models
from django.contrib.auth.models import User



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='avatars')
    linkedIn_username = models.CharField(max_length=100)
    linkedIn_password = models.CharField(max_length=100)

    def __str__(self):
        return self.user.username

def get_user_by_email(email):
    """
    Helper function to get a user by email
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None
