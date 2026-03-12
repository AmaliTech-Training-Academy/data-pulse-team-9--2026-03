import structlog
from audit.models import AuditLog
from audit.serializers import AuditLogSerializer
from rest_framework import generics

logger = structlog.get_logger(__name__)


class AuditLogListView(generics.ListAPIView):
    """
    API View to list audit logs with pagination and filtering.
    Only GET is allowed as the log is append-only.
    Filters:
    - dataset_id (int)
    - start_date (ISO 8601 string)
    - end_date (ISO 8601 string)
    """

    serializer_class = AuditLogSerializer

    def get_queryset(self):
        queryset = AuditLog.objects.all().select_related("dataset")

        dataset_id = self.request.query_params.get("dataset_id")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if dataset_id:
            queryset = queryset.filter(dataset_id=dataset_id)
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)

        logger.info(
            "audit.list_accessed",
            dataset_id=dataset_id,
            start_date=start_date,
            end_date=end_date,
            user_id=self.request.user.id if self.request.user.is_authenticated else None,
        )

        return queryset
