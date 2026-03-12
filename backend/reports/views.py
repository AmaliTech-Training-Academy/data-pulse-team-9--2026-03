"""Reports router - IMPLEMENTED."""

import json

import structlog
from checks.models import CheckResult
from checks.serializers import CheckResultResponseSerializer, QualityScoreResponseSerializer
from datapulse.exceptions import DatasetNotFoundException
from datapulse.pagination import DataPulsePagination
from datasets.models import Dataset
from django.core.cache import cache
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from reports.permissions import IsDatasetOwnerOrAdmin
from reports.serializers import QualityReportSerializer
from reports.services import report_service
from rest_framework.response import Response
from rest_framework.views import APIView

logger = structlog.get_logger(__name__)


class DatasetReportView(APIView):
    """Get a full quality report for a dataset."""

    permission_classes = [IsDatasetOwnerOrAdmin]

    @extend_schema(
        responses={200: QualityReportSerializer},
        tags=["Reports"],
        summary="Get quality report for a dataset",
    )
    def get(self, request, dataset_id):
        """Get a full quality report for a specific dataset ID."""
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found")

        self.check_object_permissions(request, dataset)

        qs = report_service.get_latest_report(dataset)

        if not qs:
            return Response(
                {"detail": f"Quality report for dataset {dataset_id} not found"},
                status=404,
            )

        results = qs.results.all()

        # Fallback: If no results are linked (old data or linkage failed),
        # fetch results for this dataset that were created around the same time.
        if not results.exists():
            from datetime import timedelta

            # Fetch results created within 5 seconds of the score
            results = CheckResult.objects.filter(
                dataset=dataset,
                checked_at__gte=qs.checked_at - timedelta(seconds=5),
                checked_at__lte=qs.checked_at + timedelta(seconds=5),
            )

        columns = []
        if dataset.column_names:
            try:
                columns = json.loads(dataset.column_names)
            except Exception:
                columns = [dataset.column_names]

        report_data = {
            "report_id": qs.id,
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "columns": columns,
            "score": qs.score,
            "total_rules": qs.total_rules,
            "passed_rules": qs.passed_rules,
            "failed_rules": qs.failed_rules,
            "results": list(CheckResultResponseSerializer(results, many=True).data),
            "checked_at": qs.checked_at,
        }

        return Response(report_data)


class QualityTrendsView(APIView):
    """Get quality score trends over time."""

    permission_classes = [IsDatasetOwnerOrAdmin]
    pagination_class = DataPulsePagination
    pagination_key = "trends"

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "start_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Filter from date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                "end_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Filter to date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                "limit",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Page size",
            ),
            OpenApiParameter(
                "page",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Page number",
            ),
        ],
        responses={200: QualityScoreResponseSerializer(many=True)},
        tags=["Reports"],
        summary="Get quality score trends for a dataset",
    )
    def get(self, request, dataset_id):
        """Get historical quality scores for a dataset with filtering and pagination."""
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found")

        self.check_object_permissions(request, dataset)

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        queryset = report_service.get_dataset_trends(dataset, start_date, end_date)

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request, view=self)
        if page is not None:
            serializer = QualityScoreResponseSerializer(page, many=True)
            return paginator.get_paginated_response(list(serializer.data))

        return Response(list(QualityScoreResponseSerializer(queryset, many=True).data))


class BulkQualityTrendsView(APIView):
    """Get quality score trends for multiple datasets over time."""

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "dataset_ids",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                description="Comma-separated list of dataset IDs",
            ),
            OpenApiParameter(
                "start_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Filter from date (YYYY-MM-DD)",
            ),
            OpenApiParameter(
                "end_date",
                OpenApiTypes.DATE,
                OpenApiParameter.QUERY,
                description="Filter to date (YYYY-MM-DD)",
            ),
        ],
        responses={200: QualityScoreResponseSerializer(many=True)},
        tags=["Reports"],
        summary="Get bulk quality score trends",
    )
    def get(self, request):
        dataset_ids_str = request.query_params.get("dataset_ids")
        if not dataset_ids_str:
            return Response({"detail": "dataset_ids parameter is required"}, status=400)

        try:
            dataset_ids = [int(id.strip()) for id in dataset_ids_str.split(",") if id.strip()]
        except ValueError:
            return Response({"detail": "Invalid dataset_ids format. Should be comma-separated integers."}, status=400)

        if getattr(request.user, "role", "USER") == "ADMIN":
            datasets = Dataset.objects.filter(id__in=dataset_ids)
        else:
            datasets = Dataset.objects.filter(id__in=dataset_ids, uploaded_by=request.user)

        if len(datasets) != len(dataset_ids):
            # Some datasets were not found or access denied
            found_ids = set(datasets.values_list("id", flat=True))
            missing_ids = set(dataset_ids) - found_ids
            logger.warning("bulk_trends.partial_results", user_id=request.user.id, missing_ids=list(missing_ids))

        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        queryset = report_service.get_bulk_dataset_trends(datasets, start_date, end_date)
        serializer = QualityScoreResponseSerializer(queryset, many=True)
        return Response(serializer.data)


class DashboardView(APIView):
    """Get latest quality scores for all datasets."""

    @extend_schema(
        responses={200: QualityScoreResponseSerializer(many=True)},
        tags=["Reports"],
        summary="Get dashboard overview",
    )
    def get(self, request):
        cache_key = f"dashboard_user_{request.user.id}"
        cached_data = cache.get(cache_key)

        if cached_data is not None:
            return Response(cached_data)

        latest_scores = report_service.get_dashboard_summary(request.user)
        data = list(QualityScoreResponseSerializer(latest_scores, many=True).data)

        # Cache for 5 minutes
        cache.set(cache_key, data, timeout=60 * 5)

        return Response(data)
