"""Reports router - IMPLEMENTED."""

from checks.serializers import CheckResultResponseSerializer, QualityScoreResponseSerializer
from datapulse.exceptions import DatasetNotFoundException
from datapulse.pagination import DataPulsePagination
from datasets.models import Dataset
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from reports.permissions import IsDatasetOwnerOrAdmin
from reports.serializers import QualityReportSerializer
from reports.services import report_service
from rest_framework.response import Response
from rest_framework.views import APIView


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
            return Response({"detail": f"Quality report for dataset {dataset_id} not found"}, status=404)

        results = qs.results.all()

        report_data = {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "score": qs.score,
            "total_rules": qs.total_rules,
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
                "start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter from date (YYYY-MM-DD)"
            ),
            OpenApiParameter(
                "end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="Filter to date (YYYY-MM-DD)"
            ),
            OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Page size"),
            OpenApiParameter("page", OpenApiTypes.INT, OpenApiParameter.QUERY, description="Page number"),
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


class DashboardView(APIView):
    """Get latest quality scores for all datasets."""

    @extend_schema(
        responses={200: QualityScoreResponseSerializer(many=True)},
        tags=["Reports"],
        summary="Get dashboard overview",
    )
    def get(self, request):
        latest_scores = report_service.get_dashboard_summary(request.user)
        return Response(list(QualityScoreResponseSerializer(latest_scores, many=True).data))
