import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flashpoll.settings")

app = Celery("flashpoll")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()   # finds tasks.py in installed apps
