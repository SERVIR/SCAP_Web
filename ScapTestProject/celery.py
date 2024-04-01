import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ScapTestProject.settings")
app = Celery("ScapTestProject")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()