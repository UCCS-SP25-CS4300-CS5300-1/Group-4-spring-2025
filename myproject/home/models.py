from django.contrib.auth.models import User
from django.db import models


class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications')
    search_word = models.CharField(max_length=100)
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    link = models.URLField(max_length=500)
    location = models.CharField(max_length=200)
    type = models.CharField(max_length=100)
    progress = models.CharField(max_length=100, default="Searched For")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.job_title} at {self.company}"


