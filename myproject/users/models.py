"""
This file contains the models for the users app.
"""

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    """
    This class contains the model for the profile.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='default.jpg', upload_to='avatars', null=True, blank=True)
    whitelisted_for_ai = models.BooleanField(default=False)

    industry_preference = models.CharField(max_length=100, blank=True, default='')
    location_preference = models.CharField(max_length=100, blank=True, default='')
    remote_preference = models.BooleanField(default=False)
    salary_min_preference = models.IntegerField(null=True, blank=True, default=0)

    objects = models.Manager()

    def __str__(self):
        return self.user.username # pylint: disable=no-member

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.user.is_superuser: # pylint: disable=no-member
                self.whitelisted_for_ai = True
        super().save(*args, **kwargs)


def get_user_by_email(email):
    """
    Helper function to get a user by email
    """
    try:
        return User.objects.get(email=email)
    except User.DoesNotExist: # pylint: disable=no-member
        return None

class Resume(models.Model):
    """
    This class contains the model for the resume.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes', null=True)
    resume = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    ai_feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Resume {self.id}"
