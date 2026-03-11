"""Report serializers matching original Pydantic schemas."""

from checks.serializers import CheckResultResponseSerializer
from rest_framework import serializers


class QualityReportSerializer(serializers.Serializer):
    report_id = serializers.IntegerField(source="id")
    dataset_id = serializers.IntegerField(source="dataset.id")
    dataset_name = serializers.CharField(source="dataset.name")
    columns = serializers.SerializerMethodField()
    score = serializers.FloatField()
    total_rules = serializers.IntegerField()
    passed_rules = serializers.IntegerField()
    failed_rules = serializers.IntegerField()
    results = CheckResultResponseSerializer(many=True)
    checked_at = serializers.DateTimeField()

    def get_columns(self, obj):
        if obj.dataset.column_names:
            return obj.dataset.column_names.split(",")
        return []
