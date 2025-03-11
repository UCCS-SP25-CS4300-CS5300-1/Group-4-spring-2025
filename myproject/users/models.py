from django.db import models
from django.contrib.auth.models import User



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='avatars', null=True, blank=True)
    linkedIn_username = models.CharField(max_length=100)
    linkedIn_password = models.CharField(max_length=100)
    whitelisted_for_ai = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    def save(self, *args, **kwargs):
        if(not self.pk):
            if(self.user.is_superuser):
                self.whitelisted_for_ai = True
        super().save(*args, **kwargs)

def get_user_by_email(email):
    """
    Helper function to get a user by email
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist:
        return None

class Resume(models.Model):
    resume = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Resume {self.id}"  