# celery.py
import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HMMontajes.settings")

app = Celery("HMMontajes")
app.conf.timezone = "America/Bogota"
app.conf.enable_utc = True

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
