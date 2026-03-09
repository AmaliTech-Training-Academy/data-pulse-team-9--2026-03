"""Quality checks router - IMPLEMENTED."""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema
from django.db.models import Q

from datasets.models import Dataset
from rules.models import ValidationRule
from checks.models import CheckResult, QualityScore
from checks.serializers import CheckResultResponseSerializer, QualityScoreResponseSerializer
from checks.services.validation_engine import ValidationEngine
from checks.services.scoring_service import calculate_quality_score
from datasets.services.file_parser import parse_csv, parse_json
from datapulse.exceptions import DatasetNotFoundException


class RunChecksView(APIView):
    """Run all applicable validation checks on a dataset."""

    @extend_schema(
        responses={200: QualityScoreResponseSerializer},
        tags=["Checks"],
        summary="Run quality checks on a dataset (TODO)",
    )
    def post(self, request, dataset_id):
        """Run all applicable validation checks on a dataset - TODO: Implement."""
        from rest_framework.exceptions import APIException
        class NotImplementedException(APIException):
            status_code = 501
            default_detail = "POST /api/checks/run not implemented"
            default_code = 'not_implemented'
        raise NotImplementedException()
        # 1. Fetch dataset
        try:
            if getattr(request.user, "role", "USER") == "ADMIN":
                dataset = Dataset.objects.get(id=dataset_id)
            else:
                dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)
        except Dataset.DoesNotExist:
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found or access denied")

        # 2. Get DatasetFile
        file_obj = dataset.files.first()
        if not file_obj:
            return Response({"detail": "No file associated with this dataset"}, status=400)

        # 3. Load file
        try:
            if dataset.file_type.lower() == "csv":
                parsed = parse_csv(file_obj.file_path)
            else:
                parsed = parse_json(file_obj.file_path)
            df = parsed["dataframe"]
        except Exception as e:
            return Response({"detail": f"Failed to parse file: {str(e)}"}, status=400)

        # 4. Fetch rules
        rules = ValidationRule.objects.filter(
            Q(dataset_type=dataset.file_type.lower()) | Q(dataset_type="all") | Q(dataset_type=""),
            is_active=True
        )

        # 5. Run checks
        engine = ValidationEngine()
        results = engine.run_all_checks(df, rules)

        # 6. Save CheckResult records
        # First, clear old results for this dataset
        CheckResult.objects.filter(dataset=dataset).delete()
        for res in results:
            rule = ValidationRule.objects.get(id=res["rule_id"])
            CheckResult.objects.create(
                dataset=dataset,
                rule=rule,
                passed=res["passed"],
                failed_rows=res["failed_rows"],
                total_rows=res["total_rows"],
                details=res["details"]
            )

        # 7. Calculate quality score
        score_data = calculate_quality_score(results, rules)

        # 8. Save QualityScore record
        QualityScore.objects.filter(dataset=dataset).delete()
        qs = QualityScore.objects.create(
            dataset=dataset,
            score=score_data["score"],
            total_rules=score_data["total_rules"],
            passed_rules=score_data["passed_rules"],
            failed_rules=score_data["failed_rules"]
        )

        # 9. Update dataset status
        dataset.status = "VALIDATED" if score_data["failed_rules"] == 0 else "FAILED"
        dataset.save()

        return Response(QualityScoreResponseSerializer(qs).data)


class CheckResultsView(APIView):
    """Get all check results for a dataset."""

    @extend_schema(
        responses={200: CheckResultResponseSerializer(many=True)},
        tags=["Checks"],
        summary="Get check results for a dataset (TODO)",
    )
    def get(self, request, dataset_id):
        """Get all check results for a dataset - TODO: Implement."""
        from rest_framework.exceptions import APIException
        class NotImplementedException(APIException):
            status_code = 501
            default_detail = "GET /api/checks/results not implemented"
            default_code = 'not_implemented'
        raise NotImplementedException()
        # Access control
        try:
            if getattr(request.user, "role", "USER") == "ADMIN":
                dataset = Dataset.objects.get(id=dataset_id)
            else:
                dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)
        except Dataset.DoesNotExist:
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found or access denied")

        results = CheckResult.objects.filter(dataset=dataset).order_by("-checked_at")
        return Response(CheckResultResponseSerializer(results, many=True).data)
