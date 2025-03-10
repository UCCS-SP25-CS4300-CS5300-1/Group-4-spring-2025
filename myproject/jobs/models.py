from django.db import models

# Create your models here.
class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    industry = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    is_remote = models.BooleanField(default=False)
    salary_min = models.IntegerField(blank=True, null=True)
    salary_max = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.title
        