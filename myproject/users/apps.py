from django.apps import AppConfig

# connects receivers for creating profile along with user
class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        import users.signals # noqa
