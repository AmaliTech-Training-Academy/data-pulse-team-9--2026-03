from rest_framework import generics, status
from rest_framework.response import Response
from schedule.models import Schedule
from schedule.serializers import ScheduleSerializer
from django_celery_beat.models import CrontabSchedule, PeriodicTask
import json

class ScheduleCreateView(generics.CreateAPIView):
    """
    API View to create a schedule for a dataset.
    Ensures a PeriodicTask is created in django-celery-beat.
    """
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            # The requirement specifically asks for 422 UNPROCESSABLE ENTITY
            # for invalid cron expressions/validation errors.
            return Response(
                {
                    "detail": "Validation error.",
                    "code": "validation_error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # We manually perform create to handle the PeriodicTask logic
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        dataset = serializer.validated_data['dataset']
        cron_expr = serializer.validated_data['cron_expression']
        
        parts = cron_expr.split()
        
        # 1. Create or Get CrontabSchedule
        crontab_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=parts[0],
            hour=parts[1],
            day_of_month=parts[2],
            month_of_year=parts[3],
            day_of_week=parts[4]
        )
        
        # 2. Create PeriodicTask (or update if already exists for this dataset)
        task_name = f"Data Quality Check - Dataset {dataset.id}"
        
        # Check if a task already exists for this dataset to avoid duplicates
        existing_task = PeriodicTask.objects.filter(name=task_name).first()
        if existing_task:
            existing_task.crontab = crontab_schedule
            existing_task.enabled = True
            existing_task.save()
            periodic_task = existing_task
        else:
            periodic_task = PeriodicTask.objects.create(
                crontab=crontab_schedule,
                name=task_name,
                task="schedule.tasks.run_scheduled_checks",
                args=json.dumps([dataset.id]),
            )
        
        # 3. Save the Schedule model link
        # If a schedule already exists for this dataset, update it
        schedule_obj, created = Schedule.objects.update_or_create(
            dataset=dataset,
            defaults={
                "cron_expression": cron_expr,
                "periodic_task": periodic_task
            }
        )
        return schedule_obj
