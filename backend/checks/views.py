"""Quality checks router - IMPLEMENTED."""

import json

import structlog
from audit.models import AuditLog
from checks.models import CheckResult, QualityScore
from checks.serializers import CheckResultResponseSerializer, QualityScoreResponseSerializer
from checks.services.scoring_service import calculate_quality_score
from checks.services.validation_engine import ValidationEngine
from datapulse.exceptions import DatasetNotFoundException
from datasets.models import Dataset
from datasets.services.file_parser import parse_csv, parse_json
from django.db import transaction
from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView
from rules.models import ValidationRule

logger = structlog.get_logger(__name__)


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
            logger.warning("checks.run.dataset_not_found", dataset_id=dataset_id)
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found or access denied")

        if dataset.status == "PROCESSING":
            logger.warning("checks.run.processing", dataset_id=dataset_id)
            return Response(
                {"detail": "Dataset is currently processing. Please wait for processing to finish."}, status=400
            )
        if dataset.status == "ERROR":
            logger.warning("checks.run.error_status", dataset_id=dataset_id)
            return Response({"detail": "Dataset parsing failed, cannot run checks."}, status=400)

        # 2. Get DatasetFile
        file_obj = dataset.files.first()
        if not file_obj:
            logger.warning("checks.run.no_file", dataset_id=dataset_id)
            return Response({"detail": "No file associated with this dataset"}, status=400)

        # 3. Load file
        try:
            if dataset.file_type.lower() == "csv":
                parsed = parse_csv(file_obj.file_path)
            else:
                parsed = parse_json(file_obj.file_path)
            df = parsed["dataframe"]
        except Exception as e:
            dataset.status = "FAILED"
            dataset.save()
            return Response({"detail": f"Failed to parse file: {str(e)}"}, status=400)

        # 4. Fetch rules
        rules = ValidationRule.objects.filter(
            Q(dataset_type=dataset.file_type.lower()) | Q(dataset_type="all") | Q(dataset_type=""), is_active=True
        )

        # 5. Run checks
        try:
            engine = ValidationEngine()
            results = engine.run_all_checks(df, rules)
        except Exception:
            logger.exception("checks.run.failed", dataset_id=dataset.id)
            dataset.status = "FAILED"
            dataset.save()
            return Response({"detail": "Validation engine execution failed."}, status=500)

        # 6. Save CheckResult records and score atomically
        with transaction.atomic():
            # Map rules for fast O(1) lookup
            rules_map = {r.id: r for r in rules}

            # 7. Calculate quality score
            score_data = calculate_quality_score(results, rules)

            # 8. Save QualityScore record
            qs = QualityScore.objects.create(
                dataset=dataset,
                score=score_data["score"],
                total_rules=score_data["total_rules"],
                passed_rules=score_data["passed_rules"],
                failed_rules=score_data["failed_rules"],
            )

            check_results_to_create = []
            for res in results:
                rule = rules_map.get(res["rule_id"])
                if not rule:
                    continue

                details_json = json.dumps({"message": res.get("details", ""), "samples": res.get("samples", [])})

                check_results_to_create.append(
                    CheckResult(
                        dataset=dataset,
                        rule=rule,
                        quality_score=qs,
                        passed=res["passed"],
                        failed_rows=res["failed_rows"],
                        total_rows=res["total_rows"],
                        details=details_json,
                    )
                )

            # Bulk create all results at once to save DML queries
            CheckResult.objects.bulk_create(check_results_to_create)

            # 9. Link or Update audit log
            # Since this is the manual run endpoint, we record 'manual' and the user's email if available.
            triggered_by = getattr(request.user, "email", "unknown_user")
            AuditLog.objects.create(
                dataset=dataset, triggered_by=triggered_by, trigger_type="manual", score=score_data["score"]
            )

            # 10. Update dataset status
            dataset.status = "VALIDATED" if score_data["failed_rules"] == 0 else "FAILED"
            dataset.save()

            logger.info(
                "checks.run.success",
                dataset_id=dataset.id,
                score=score_data["score"],
                failed_rules=score_data["failed_rules"],
                user_id=request.user.id if request.user.is_authenticated else None,
            )

        return Response(QualityScoreResponseSerializer(qs).data)


class CheckResultsView(APIView):
    """Get all check results for a dataset."""

    @extend_schema(
        responses={200: CheckResultResponseSerializer(many=True)},
        tags=["Checks"],
        summary="Get check results for a dataset",
    )
    def get(self, request, dataset_id):
        """Get all check results for a dataset."""

        # Access control
        try:
            if getattr(request.user, "role", "USER") == "ADMIN":
                dataset = Dataset.objects.get(id=dataset_id)
            else:
                dataset = Dataset.objects.get(id=dataset_id, uploaded_by=request.user)
        except Dataset.DoesNotExist:
            logger.warning("checks.results.dataset_not_found", dataset_id=dataset_id)
            raise DatasetNotFoundException(f"Dataset {dataset_id} not found or access denied")

        results = CheckResult.objects.filter(dataset=dataset).order_by("-checked_at")
        if not results.exists():
            logger.warning("checks.no_results", dataset_id=dataset.id)

        logger.info(
            "checks.results_accessed",
            dataset_id=dataset.id,
            user_id=request.user.id if request.user.is_authenticated else None,
        )
        return Response(list(CheckResultResponseSerializer(results, many=True).data))
