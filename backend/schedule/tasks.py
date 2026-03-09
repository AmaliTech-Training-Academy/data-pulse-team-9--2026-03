import structlog
from celery import shared_task
from checks.models import CheckResult, QualityScore
from checks.services.scoring_service import calculate_quality_score
from checks.services.validation_engine import ValidationEngine
from datasets.models import Dataset
from datasets.services.file_parser import parse_csv, parse_json
from django.db.models import Q
from rules.models import ValidationRule

logger = structlog.get_logger(__name__)


@shared_task(name="schedule.tasks.run_scheduled_checks")
def run_scheduled_checks(dataset_id):
    """
    Background task to run quality checks for a specific dataset.
    Produces results identical to manually triggered checks.
    """
    logger.info("scheduled_checks.started", dataset_id=dataset_id)
    try:
        # 1. Fetch dataset
        dataset = Dataset.objects.get(id=dataset_id)

        # 2. Get DatasetFile
        file_obj = dataset.files.first()
        if not file_obj:
            logger.error("scheduled_checks.no_file", dataset_id=dataset_id)
            return

        # 3. Load file
        try:
            if dataset.file_type.lower() == "csv":
                parsed = parse_csv(file_obj.file_path)
            else:
                parsed = parse_json(file_obj.file_path)
            df = parsed["dataframe"]
        except Exception as e:
            logger.error("scheduled_checks.parse_failed", dataset_id=dataset_id, error=str(e))
            return

        # 4. Fetch rules
        rules = ValidationRule.objects.filter(
            Q(dataset_type=dataset.file_type.lower()) | Q(dataset_type="all") | Q(dataset_type=""),
            is_active=True,
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
                details=res["details"],
            )

        # 7. Calculate quality score
        score_data = calculate_quality_score(results, rules)

        # 8. Save QualityScore record
        QualityScore.objects.filter(dataset=dataset).delete()
        QualityScore.objects.create(
            dataset=dataset,
            score=score_data["score"],
            total_rules=score_data["total_rules"],
            passed_rules=score_data["passed_rules"],
            failed_rules=score_data["failed_rules"],
        )

        # 9. Update dataset status
        dataset.status = "VALIDATED" if score_data["failed_rules"] == 0 else "FAILED"
        dataset.save()

        logger.info("scheduled_checks.success", dataset_id=dataset_id, score=score_data["score"])

    except Dataset.DoesNotExist:
        logger.error("scheduled_checks.not_found", dataset_id=dataset_id)
    except Exception as e:
        logger.exception("scheduled_checks.failed", dataset_id=dataset_id, error=str(e))
