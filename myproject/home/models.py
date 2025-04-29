from django.contrib.auth.models import User
from django.db import models

## don't use this, needs to get removed
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

## use this for mocking Matt
class JobListing(models.Model):
    job_id = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    company_logo = models.URLField(max_length=500, null=True, blank=True)
    job_type = models.CharField(max_length=50, null=True, blank=True)
    industry = models.CharField(max_length=100, null=True, blank=True)
    job_level = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    url = models.URLField(max_length=500, null=True, blank=True)
    salary_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=3, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Cache-related fields
    search_key = models.CharField(max_length=255, db_index=True, blank=True)

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['search_key']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company}"

    @property
    def salary_display(self):
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f} - {self.salary_max:,.0f} {self.salary_currency}"
        elif self.salary_min:
            return f"From {self.salary_min:,.0f} {self.salary_currency}"
        elif self.salary_max:
            return f"Up to {self.salary_max:,.0f} {self.salary_currency}"
        return None

class UserJobInteraction(models.Model):
    """Tracks user interactions with job listings (viewed, applied)."""
    INTERACTION_TYPES = (
        ('viewed', 'Viewed'),
        ('applied', 'Applied'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_interactions')
    job = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name='user_interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job', 'interaction_type')
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.job.title}"


