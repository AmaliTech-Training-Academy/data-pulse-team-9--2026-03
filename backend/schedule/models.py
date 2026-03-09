from datasets.models import Dataset
from django.db import models
from django_celery_beat.models import PeriodicTask


class Schedule(models.Model):
    """Schedule linked to a dataset for periodic quality checks."""

    dataset = models.OneToOneField(Dataset, on_delete=models.CASCADE, related_name="schedule")
    cron_expression = models.CharField(max_length=100)
    periodic_task = models.OneToOneField(PeriodicTask, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "schedules"

    def __str__(self):
        return f"Schedule for {self.dataset.name}: {self.cron_expression}"
