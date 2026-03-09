"""Production settings."""

from .base import *

DEBUG = env.bool("DEBUG", default=False)

# Strict allowed hosts required for production
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost"])

# Secure CORS config (origin whitelist)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True

# Ensure only JSON responses in production
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (
    "rest_framework.renderers.JSONRenderer",
)

# Secure Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Use strictly JSON formatted structlog output in prod (easily parsable by ELK/Datadog)
import structlog
LOGGING["formatters"]["structlog_formatter"]["processors"].append(
    structlog.processors.JSONRenderer()
)
