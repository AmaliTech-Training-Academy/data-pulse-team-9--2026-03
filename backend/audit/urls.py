from audit.views import AuditLogListView
from django.urls import path

urlpatterns = [
    path("", AuditLogListView.as_view(), name="audit-log-list"),
]
