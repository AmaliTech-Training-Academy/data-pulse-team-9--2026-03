"""Check result serializers matching original Pydantic schemas."""

import json

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

    def _clean_nan(self, data):
        """Recursively replace NaN float values with None for JSON compliance."""
        import math

        if isinstance(data, dict):
            return {k: self._clean_nan(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_nan(x) for x in data]
        elif isinstance(data, float) and math.isnan(data):
            return None
        return data

    def get_sample_rows(self, obj):
        try:
            if not obj.details:
                return []
            data = json.loads(obj.details)
            samples = data.get("samples", [])
            return self._clean_nan(samples)
        except (ValueError, TypeError):
            return []

    def get_details(self, obj):
        try:
            import json

            if not obj.details:
                return ""
            data = json.loads(obj.details)
            return data.get("message", obj.details)
        except (ValueError, TypeError):
            return obj.details


class QualityScoreResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    dataset_id = serializers.IntegerField(source="dataset.id")
    score = serializers.FloatField(required=False, allow_null=True)
    total_rules = serializers.IntegerField(required=False, allow_null=True)
    passed_rules = serializers.IntegerField(required=False, allow_null=True)
    failed_rules = serializers.IntegerField(required=False, allow_null=True)
    checked_at = serializers.DateTimeField(required=False, allow_null=True)
