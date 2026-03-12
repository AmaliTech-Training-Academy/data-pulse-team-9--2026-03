"""Celery configuration for DataPulse."""

import os

import django
from celery import Celery

# from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datapulse.settings.prod")


django.setup()

app = Celery("datapulse")

# Read config from Django settings with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
