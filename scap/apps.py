from django.apps import AppConfig


class ScapConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'scap'

    def ready(self):
        import scap.signals  # Ensure the signals are registered
