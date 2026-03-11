"""DataPulse URL Configuration."""

from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class RootView(APIView):
    """Root endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"name": "DataPulse", "version": "1.0.0", "docs": "/docs"})


class MetricsProxyView(APIView):
    """Prometheus Metrics Endpoint."""

    permission_classes = [AllowAny]

    @extend_schema(
        responses={200: str},
        summary="Get Prometheus App Metrics",
        description="Returns application performance and health metrics in Prometheus exposition format for scraping by Grafana.",
    )
    def get(self, request):
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


class HealthCheckView(APIView):
    """Health check endpoint."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "healthy"})


urlpatterns = [
    # Built-in Admin
    path("admin/", admin.site.urls),
    path("metrics/", MetricsProxyView.as_view(), name="metrics"),
    # Root & Health
    path("", RootView.as_view(), name="root"),
    path("health/", HealthCheckView.as_view(), name="health"),
    # API
    path("api/auth/", include("authentication.urls")),
    path("api/datasets/", include("datasets.urls")),
    path("api/rules/", include("rules.urls")),
    path("api/checks/", include("checks.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/schedules/", include("schedule.urls")),
    path("api/audit/", include("audit.urls")),
    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
