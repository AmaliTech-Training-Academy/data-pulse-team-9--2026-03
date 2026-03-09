"""Report serializers matching original Pydantic schemas."""

from rest_framework import serializers
from checks.serializers import CheckResultResponseSerializer


class QualityReportSerializer(serializers.Serializer):
    dataset_id = serializers.IntegerField()
    dataset_name = serializers.CharField()
    score = serializers.FloatField()
    total_rules = serializers.IntegerField()
    results = CheckResultResponseSerializer(many=True)
    checked_at = serializers.DateTimeField()
