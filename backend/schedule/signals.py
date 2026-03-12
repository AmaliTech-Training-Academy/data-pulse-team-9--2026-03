import json

from datasets.models import Dataset
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from schedule.models import AlertConfig, Schedule  # noqa: F401


@receiver(post_save, sender=Dataset)
def create_default_schedule(sender, instance, created, **kwargs):
    """
    Automatically initialize a default midnight schedule for every new dataset.
    """
    if created:
        cron_expr = "0 0 * * *"

        # 1. Create or Get CrontabSchedule for midnight daily
        crontab_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="0", hour="0", day_of_month="*", month_of_year="*", day_of_week="*"
        )

        # 2. Create PeriodicTask for celery beat
        task_name = f"Data Quality Check - Dataset {instance.id}"
        periodic_task, _ = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                "crontab": crontab_schedule,
                "task": "schedule.tasks.run_scheduled_checks",
                "args": json.dumps([instance.id]),
                "enabled": True,
            },
        )

        # 3. Create the proxy Schedule model
        Schedule.objects.get_or_create(
            dataset=instance, defaults={"cron_expression": cron_expr, "periodic_task": periodic_task}
        )
