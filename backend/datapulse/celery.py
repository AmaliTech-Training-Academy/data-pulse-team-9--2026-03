"""Celery configuration for DataPulse."""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datapulse.settings.prod")

app = Celery("datapulse")

# Read config from Django settings with CELERY_ prefix
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Default beat schedule — runs the scheduled checks every hour.
# The actual per-dataset frequency is controlled by ScheduleConfig model.
app.conf.beat_schedule = {
    "run-scheduled-quality-checks": {
        "task": "schedule.tasks.run_scheduled_checks",
        "schedule": crontab(minute=0),  # Every hour at :00
    },
}
