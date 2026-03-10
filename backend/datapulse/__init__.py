"""DataPulse project — ensure Celery app is loaded on Django startup."""

from .celery import app as celery_app

__all__ = ("celery_app",)
