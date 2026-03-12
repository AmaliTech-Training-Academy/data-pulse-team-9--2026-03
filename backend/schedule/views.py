import json

from datasets.models import Dataset
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from rest_framework import generics, status
from rest_framework.response import Response
from schedule.models import AlertConfig, Schedule
from schedule.serializers import AlertConfigSerializer, ScheduleSerializer


class ScheduleCreateView(generics.ListCreateAPIView):
    """
    API View to create or list schedules for datasets.
    Ensures a PeriodicTask is created/managed in django-celery-beat.
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
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # We manually perform create to handle the PeriodicTask logic
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        dataset = serializer.validated_data["dataset"]
        cron_expr = serializer.validated_data["cron_expression"]

        parts = cron_expr.split()

        # 1. Create or Get CrontabSchedule
        crontab_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute=parts[0], hour=parts[1], day_of_month=parts[2], month_of_year=parts[3], day_of_week=parts[4]
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
            dataset=dataset, defaults={"cron_expression": cron_expr, "periodic_task": periodic_task}
        )
        serializer.instance = schedule_obj
        return schedule_obj


class ScheduleDetailView(generics.RetrieveDestroyAPIView):
    """
    API View to retrieve or delete a schedule.
    Deletion of Schedule will also delete the linked PeriodicTask via CASCADE.
    """

    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    def perform_destroy(self, instance):
        if instance.periodic_task:
            instance.periodic_task.delete()
        instance.delete()


class ScheduleToggleView(generics.UpdateAPIView):
    """
    API View to pause or resume a schedule by toggling the enabled state
    of the linked PeriodicTask.
    """

    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer

    def patch(self, request, *args, **kwargs):
        action = self.kwargs.get("action")
        schedule = self.get_object()
        periodic_task = schedule.periodic_task

        if not periodic_task:
            return Response({"detail": "No periodic task linked to this schedule"}, status=status.HTTP_400_BAD_REQUEST)

        if action == "pause":
            periodic_task.enabled = False
            periodic_task.save()
            return Response({"status": "paused", "schedule_id": schedule.id})

        if action == "resume":
            periodic_task.enabled = True
            periodic_task.save()
            return Response({"status": "resumed", "schedule_id": schedule.id})

        return Response({"detail": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)


class AlertConfigView(generics.CreateAPIView):
    """
    API View to set or update an alert threshold for a dataset.
    Endpoint: POST /alerts/{dataset_id}
    """

    queryset = AlertConfig.objects.all()
    serializer_class = AlertConfigSerializer
    lookup_field = "dataset_id"

    def post(self, request, *args, **kwargs):
        dataset_id = self.kwargs.get("dataset_id")
        try:
            dataset = Dataset.objects.get(id=dataset_id)
        except Dataset.DoesNotExist:
            return Response({"detail": "Dataset not found."}, status=status.HTTP_404_NOT_FOUND)

        # We use update_or_create to handle both setting and updating the threshold
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "detail": "Validation error.",
                    "code": "validation_error",
                    "errors": serializer.errors,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        threshold = serializer.validated_data["threshold"]
        alert_config, created = AlertConfig.objects.update_or_create(dataset=dataset, defaults={"threshold": threshold})

        # Set is_alert_active to False when updating/creating threshold to allow re-alerting if needed
        # Or keep its state? Requirement implies "Repeat alerts are suppressed until ... recovers".
        # Resetting it on threshold change is a reasonable default.
        alert_config.is_alert_active = False
        alert_config.save()

        response_serializer = self.get_serializer(alert_config)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
