"""Production settings."""

from .base import *

DEBUG = env.bool("DEBUG", default=False)

# Strict allowed hosts required for production
# Allow ALB health checks from private IPs and ALB DNS
ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        ".elb.amazonaws.com",  # Allow all ALB DNS names
        ".amplifyapp.com",  # Allow Amplify frontend
    ],
)

# Also allow private IPs from VPC for health checks
import socket

try:
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    if local_ip not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(local_ip)
except Exception:
    pass

# Secure CORS config (origin whitelist)
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True

# Ensure only JSON responses in production
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ("rest_framework.renderers.JSONRenderer",)

# Secure Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Use strictly JSON formatted structlog output in prod (easily parsable by ELK/Datadog)
import structlog

LOGGING["formatters"]["structlog_formatter"]["processors"].append(structlog.processors.JSONRenderer())
