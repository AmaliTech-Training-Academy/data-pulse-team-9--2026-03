"""DataPulse URL Configuration."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    # Built-in Admin
    path("admin/", admin.site.urls),
    # Core (Root, Health, Metrics)
    path("", include("core.urls")),
    # API
    path("api/auth/", include("authentication.urls")),
    path("api/datasets/", include("datasets.urls")),
    path("api/rules/", include("rules.urls")),
    path("api/checks/", include("checks.urls")),
    path("api/reports/", include("reports.urls")),
    path("api/schedules/", include("schedule.urls")),
    # Swagger / OpenAPI
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
