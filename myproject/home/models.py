from django.contrib.auth.models import User
from django.db import models


PROGRESS_CHOICES = [
    ("U", "Unfinished"),
    ("F", "Finished"),
]


# Create your models here.
class Application(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_word = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    link = models.URLField(max_length=200, blank=True)
    type = models.CharField(max_length=100)
    progress = models.CharField(max_length=100, choices=PROGRESS_CHOICES)


