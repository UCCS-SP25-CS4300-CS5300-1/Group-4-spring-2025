"""
This file contains the config for the jobs app.
"""

from django.apps import AppConfig


class JobsConfig(AppConfig):
    """
    This class contains the config for the jobs app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
