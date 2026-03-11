from celery.schedules import crontab
from datasets.models import Dataset
from rest_framework import serializers
from schedule.models import AlertConfig, Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    dataset_id = serializers.PrimaryKeyRelatedField(queryset=Dataset.objects.all(), source="dataset")
    is_active = serializers.SerializerMethodField()
    last_run = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = ["id", "dataset_id", "cron_expression", "is_active", "last_run", "created_at", "updated_at"]
        read_only_fields = ["id", "is_active", "last_run", "created_at", "updated_at"]

    def get_is_active(self, obj):
        return obj.periodic_task.enabled if obj.periodic_task else False

    def get_last_run(self, obj):
        return obj.periodic_task.last_run_at if obj.periodic_task else None

    def validate_cron_expression(self, value):
        """
        Validate that the cron expression is a valid 5-part crontab.
        """
        parts = value.split()
        if len(parts) != 5:
            raise serializers.ValidationError(
                "Cron expression must have exactly 5 parts (minute, hour, day of month, month, day of week)."
            )

        try:
            # We use celery's crontab helper to validate the components
            crontab(minute=parts[0], hour=parts[1], day_of_month=parts[2], month_of_year=parts[3], day_of_week=parts[4])
        except Exception as e:
            # Re-raise as ValidationError so it's handled by DRF
            raise serializers.ValidationError(f"Invalid cron expression: {str(e)}")

        return value


class AlertConfigSerializer(serializers.ModelSerializer):
    dataset_id = serializers.PrimaryKeyRelatedField(queryset=Dataset.objects.all(), source="dataset", required=False)

    class Meta:
        model = AlertConfig
        fields = ["id", "dataset_id", "threshold", "is_alert_active", "created_at", "updated_at"]
        read_only_fields = ["id", "is_alert_active", "created_at", "updated_at"]

    def validate_threshold(self, value):
        if not (0 <= value <= 100):
            raise serializers.ValidationError("Threshold must be between 0 and 100.")
        return value
