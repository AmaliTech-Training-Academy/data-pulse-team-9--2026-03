from django.urls import path

from .views import HealthCheckView, MetricsProxyView, RootView

urlpatterns = [
    path("", RootView.as_view(), name="root"),
    path("health/", HealthCheckView.as_view(), name="health"),
    path("metrics/", MetricsProxyView.as_view(), name="metrics"),
]
