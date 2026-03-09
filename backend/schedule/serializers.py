from celery.schedules import crontab
from datasets.models import Dataset
from rest_framework import serializers
from schedule.models import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    dataset_id = serializers.PrimaryKeyRelatedField(queryset=Dataset.objects.all(), source="dataset")

    class Meta:
        model = Schedule
        fields = ["id", "dataset_id", "cron_expression", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

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
