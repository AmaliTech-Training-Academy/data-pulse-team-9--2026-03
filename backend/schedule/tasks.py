import structlog
from celery import shared_task
from checks.models import CheckResult, QualityScore
from checks.services.scoring_service import calculate_quality_score
from checks.services.validation_engine import ValidationEngine
from datasets.models import Dataset
from datasets.services.file_parser import parse_csv, parse_json
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from rules.models import ValidationRule
from schedule.models import AlertConfig

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

        # 10. Check Alert Threshold and Send Email
        _handle_alerts(dataset, score_data["score"])

        logger.info("scheduled_checks.success", dataset_id=dataset_id, score=score_data["score"])

    except Dataset.DoesNotExist:
        logger.error("scheduled_checks.not_found", dataset_id=dataset_id)
    except Exception as e:
        logger.exception("scheduled_checks.failed", dataset_id=dataset_id, error=str(e))


def _handle_alerts(dataset, current_score):
    """Internal helper to handle threshold checking and email alerting."""
    try:
        alert_config = AlertConfig.objects.get(dataset=dataset)
    except AlertConfig.DoesNotExist:
        return

    threshold = alert_config.threshold

    if current_score < threshold:
        if not alert_config.is_alert_active and alert_config.email_notifications:
            # Send alert email
            subject = f"Data Quality Alert: {dataset.name}"
            report_url = f"{settings.FRONTEND_URL}/reports/{dataset.id}"
            message = (
                f"The quality score for dataset '{dataset.name}' has dropped below the threshold.\n\n"
                f"Current Score: {current_score}\n"
                f"Threshold: {threshold}\n\n"
                f"View the full report here: {report_url}"
            )

            # Note: We should ideally have the user's email, but for now we'll use a placeholder or system admin
            # The requirement doesn't specify the recipient, so we'll use a mocked recipient or settings default
            recipient_list = [dataset.uploaded_by.email] if dataset.uploaded_by and dataset.uploaded_by.email else []

            if recipient_list:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    recipient_list,
                    fail_silently=False,
                )
                logger.info("alert_email.sent", dataset_id=dataset.id, score=current_score)

            # Suppress future alerts until recovery
            alert_config.is_alert_active = True
            alert_config.save()
    else:
        # Score is above threshold, reset suppression if it was active
        if alert_config.is_alert_active:
            alert_config.is_alert_active = False
            alert_config.save()
            logger.info("alert_status.recovered", dataset_id=dataset.id, score=current_score)
