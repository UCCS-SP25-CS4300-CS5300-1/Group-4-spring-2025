"""
This file contains the config for the users app.
"""

from django.apps import AppConfig


class UsersConfig(AppConfig):
    """
    This class contains the config for the users app.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals # pylint: disable=import-error,unused-import,import-outside-toplevel
