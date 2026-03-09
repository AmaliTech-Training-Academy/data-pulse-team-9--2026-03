"""Check result serializers matching original Pydantic schemas."""

from rest_framework import serializers


class CheckResultResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    dataset_id = serializers.IntegerField(source="dataset.id")
    rule_id = serializers.IntegerField(source="rule.id")
    passed = serializers.BooleanField()
    failed_rows = serializers.IntegerField()
    total_rows = serializers.IntegerField()
    details = serializers.CharField(allow_null=True)
    checked_at = serializers.DateTimeField()


class QualityScoreResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    dataset_id = serializers.IntegerField(source="dataset.id")
    score = serializers.FloatField()
    total_rules = serializers.IntegerField()
    passed_rules = serializers.IntegerField()
    failed_rules = serializers.IntegerField()
    checked_at = serializers.DateTimeField()
