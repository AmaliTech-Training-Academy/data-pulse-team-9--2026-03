"""Check result serializers matching original Pydantic schemas."""

from rest_framework import serializers


class CheckResultResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    dataset_id = serializers.IntegerField(source="dataset.id")
    rule_id = serializers.IntegerField(source="rule.id")
    rule_name = serializers.CharField(source="rule.name")
    passed = serializers.BooleanField()
    fail_count = serializers.IntegerField(source="failed_rows")
    pass_count = serializers.SerializerMethodField()
    sample_rows = serializers.SerializerMethodField()
    details = serializers.SerializerMethodField()
    checked_at = serializers.DateTimeField()

    def get_pass_count(self, obj):
        return obj.total_rows - obj.failed_rows

    def get_sample_rows(self, obj):
        try:
            import json

            data = json.loads(obj.details)
            return data.get("samples", [])
        except (ValueError, TypeError):
            return []

    def get_details(self, obj):
        try:
            import json

            data = json.loads(obj.details)
            return data.get("message", obj.details)
        except (ValueError, TypeError):
            return obj.details


class QualityScoreResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    dataset_id = serializers.IntegerField(source="dataset.id")
    score = serializers.FloatField()
    total_rules = serializers.IntegerField()
    passed_rules = serializers.IntegerField()
    failed_rules = serializers.IntegerField()
    checked_at = serializers.DateTimeField()
