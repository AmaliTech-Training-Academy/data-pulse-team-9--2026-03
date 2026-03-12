import redis
import structlog
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

logger = structlog.get_logger(__name__)


class RootView(APIView):
    """Root endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"name": "DataPulse", "version": "1.0.0", "docs": "/docs"})


class MetricsProxyView(APIView):
    """Prometheus Metrics Endpoint."""

    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        responses={200: str},
        summary="Get Prometheus App Metrics",
        description="Returns application performance and health metrics in Prometheus exposition format for scraping by Grafana.",
    )
    def get(self, request):
        logger.info("metrics.accessed")
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


class HealthCheckView(APIView):
    """Robust Health check endpoint."""

    permission_classes = [AllowAny]
    throttle_classes = []

    @extend_schema(
        responses={200: dict, 503: dict},
        summary="System Health Check",
        description="Pings PostgreSQL and Redis to verify overall system health.",
    )
    def get(self, request):
        health_status = {"status": "healthy", "database": "down", "redis": "down"}
        is_healthy = True

        # Check Database
        db_conn = connections["default"]
        try:
            with db_conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
            health_status["database"] = "up"
        except (OperationalError, Exception) as e:
            logger.error("healthcheck.database.failed", error=str(e))
            is_healthy = False

        # Check Redis
        try:
            r = redis.from_url(settings.CELERY_BROKER_URL, socket_timeout=2)
            if r.ping():
                health_status["redis"] = "up"
            else:
                raise Exception("Redis ping returned False")
        except Exception as e:
            logger.error("healthcheck.redis.failed", error=str(e))
            is_healthy = False

        if is_healthy:
            logger.info("healthcheck.status", result="healthy")
            return Response(health_status, status=status.HTTP_200_OK)
        else:
            logger.warning("healthcheck.status", result="unhealthy", details=health_status)
            health_status["status"] = "unhealthy"
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
