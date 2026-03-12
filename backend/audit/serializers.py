from audit.models import AuditLog
from rest_framework import serializers


class AuditLogSerializer(serializers.ModelSerializer):
    dataset_name = serializers.CharField(source="dataset.name", read_only=True)

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "dataset",
            "dataset_name",
            "triggered_by",
            "trigger_type",
            "score",
            "timestamp",
        ]
