"""Development settings."""

from .base import *

DEBUG = env.bool("DEBUG", default=True)

ALLOWED_HOSTS = ["*"]


# Run Celery tasks synchronously in dev/test (no broker needed)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Relaxed CORS for local dev
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Use console email backend for development to see emails in logs
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# Disable static file compression in development
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# When running in dev, enable the Browsable API
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Use human-readable coloring for structlog in dev
import structlog

LOGGING["formatters"]["structlog_formatter"]["processors"].append(structlog.dev.ConsoleRenderer())
