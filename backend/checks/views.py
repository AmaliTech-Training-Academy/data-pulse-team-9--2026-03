"""Quality checks router - IMPLEMENTED."""

from checks.models import CheckResult, QualityScore
from checks.serializers import CheckResultResponseSerializer, QualityScoreResponseSerializer
from checks.services.scoring_service import calculate_quality_score
from checks.services.validation_engine import ValidationEngine
from datapulse.exceptions import DatasetNotFoundException
from datasets.models import Dataset
from datasets.services.file_parser import parse_csv, parse_json
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.models import ValidationRule


class RunChecksView(APIView):
    """Run all applicable validation checks on a dataset."""

    @extend_schema(
        responses={200: QualityScoreResponseSerializer},
        tags=["Checks"],
        summary="Run quality checks on a dataset",
    )
    def post(self, request, dataset_id):
        """Run all applicable validation checks on a dataset."""
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
            Q(dataset_type=dataset.file_type.lower()) | Q(dataset_type="all") | Q(dataset_type=""), is_active=True
        )

        # 5. Run checks
        engine = ValidationEngine()
        results = engine.run_all_checks(df, rules)

        # 6. Calculate quality score
        score_data = calculate_quality_score(results, rules)

        # 7. Save QualityScore record (The "Report" entry)
        import json

        qs = QualityScore.objects.create(
            dataset=dataset,
            score=score_data["score"],
            total_rules=score_data["total_rules"],
            passed_rules=score_data["passed_rules"],
            failed_rules=score_data["failed_rules"],
        )

        # 8. Save CheckResult records linked to this run
        for res in results:
            rule = ValidationRule.objects.get(id=res["rule_id"])

            # Combine details and samples into a JSON structure
            result_details = {"message": res["details"], "samples": res.get("samples", [])}

            CheckResult.objects.create(
                dataset=dataset,
                rule=rule,
                quality_score=qs,
                passed=res["passed"],
                failed_rows=res["failed_rows"],
                total_rows=res["total_rows"],
                details=json.dumps(result_details),
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
        # Access control
        # Access control
        try:
            if getattr(request.user, "role", "USER") == "ADMIN":
                dataset = Dataset.objects.get(id=dataset_id)
            else:
                dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)
        except Dataset.DoesNotExist:
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found or access denied")

        results = CheckResult.objects.filter(dataset=dataset).order_by("-checked_at")
        return Response(list(CheckResultResponseSerializer(results, many=True).data))
