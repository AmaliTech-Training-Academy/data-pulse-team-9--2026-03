"""Reports router - IMPLEMENTED."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from datetime import datetime, timedelta
from django.utils import timezone

from reports.serializers import QualityReportSerializer
from checks.serializers import QualityScoreResponseSerializer, CheckResultResponseSerializer
from datasets.models import Dataset
from checks.models import QualityScore, CheckResult
from datapulse.exceptions import DatasetNotFoundException


class DatasetReportView(APIView):
    """Get a full quality report for a dataset."""

    @extend_schema(
        responses={200: QualityReportSerializer},
        tags=["Reports"],
        summary="Get quality report for a dataset (TODO)",
    )
    def get(self, request, dataset_id):
        """Get a full quality report for a dataset - TODO: Implement."""
        from rest_framework.exceptions import APIException
        class NotImplementedException(APIException):
            status_code = 501
            default_detail = "GET /api/reports/{id} not implemented"
            default_code = 'not_implemented'
        raise NotImplementedException()
        try:
            if getattr(request.user, "role", "USER") == "ADMIN":
                dataset = Dataset.objects.get(id=dataset_id)
            else:
                dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)
        except Dataset.DoesNotExist:
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found or access denied")

        qs = QualityScore.objects.filter(dataset=dataset).order_by("-checked_at").first()
        if not qs:
            return Response({"detail": "No quality score found for this dataset"}, status=404)

        results = CheckResult.objects.filter(dataset=dataset).order_by("-checked_at")
        
        report_data = {
            "dataset_id": dataset.id,
            "dataset_name": dataset.name,
            "score": qs.score,
            "total_rules": qs.total_rules,
            "results": CheckResultResponseSerializer(results, many=True).data,
            "checked_at": qs.checked_at
        }
        
        return Response(report_data)


class QualityTrendsView(APIView):
    """Get quality score trends over time."""

    @extend_schema(
        parameters=[
            OpenApiParameter("days", OpenApiTypes.INT, OpenApiParameter.QUERY, default=30),
        ],
        responses={200: QualityScoreResponseSerializer(many=True)},
        tags=["Reports"],
        summary="Get quality score trends (TODO)",
    )
    def get(self, request):
        """Get quality score trends over time - TODO: Implement."""
        from rest_framework.exceptions import APIException
        class NotImplementedException(APIException):
            status_code = 501
            default_detail = "GET /api/reports/trends not implemented"
            default_code = 'not_implemented'
        raise NotImplementedException()
        days = int(request.query_params.get("days", 30))
        start_date = timezone.now() - timedelta(days=days)
        
        if getattr(request.user, "role", "USER") == "ADMIN":
            queryset = QualityScore.objects.filter(checked_at__gte=start_date).order_by("checked_at")
        else:
            queryset = QualityScore.objects.filter(
                dataset__uploaded_by=request.user,
                checked_at__gte=start_date
            ).order_by("checked_at")

        return Response(QualityScoreResponseSerializer(queryset, many=True).data)


class DashboardView(APIView):
    """Get latest quality scores for all datasets."""

    @extend_schema(
        responses={200: QualityScoreResponseSerializer(many=True)},
        tags=["Reports"],
        summary="Get dashboard overview",
    )
    def get(self, request):
        if getattr(request.user, "role", "USER") == "ADMIN":
            datasets = Dataset.objects.all()
        else:
            datasets = Dataset.objects.filter(uploaded_by=request.user)
            
        latest_scores = []
        for dataset in datasets:
            qs = QualityScore.objects.filter(dataset=dataset).order_by("-checked_at").first()
            if qs:
                latest_scores.append(qs)
                
        return Response(QualityScoreResponseSerializer(latest_scores, many=True).data)
