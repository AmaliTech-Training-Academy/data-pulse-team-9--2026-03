from django.db import models


class AuditLog(models.Model):
    """
    Append-only log of all quality check runs.
    Records the trigger source, dataset, score, and timestamp.
    """

    TRIGGER_TYPES = [
        ("manual", "Manual"),
        ("scheduled", "Scheduled"),
    ]

    dataset = models.ForeignKey("datasets.Dataset", on_delete=models.CASCADE, related_name="audit_logs")
    triggered_by = models.CharField(max_length=255)  # user email or 'system'
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES)
    score = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.trigger_type.capitalize()} check for {self.dataset.name} at {self.timestamp}"

    def save(self, *args, **kwargs):
        if self.pk:
            # Prevent updates to existing audit logs
            raise RuntimeError("AuditLog entries are append-only and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deletion of audit logs
        raise RuntimeError("AuditLog entries are append-only and cannot be deleted.")
