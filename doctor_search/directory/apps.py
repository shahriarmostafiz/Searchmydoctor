from django.apps import AppConfig


class DirectoryConfig(AppConfig):
    name = "doctor_search.directory"
    # name = 'directory'
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa
