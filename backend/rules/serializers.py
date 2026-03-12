from rest_framework import serializers
from rules.models import ValidationRule


class RuleCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationRule
        fields = ["name", "dataset_type", "field_name", "rule_type", "parameters", "severity"]

    def validate_parameters(self, value):
        if not value or not str(value).strip():
            return value
        import json
        import re

        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            # Auto-fix unescaped backslashes often sent by Swagger for regex rules
            fixed_value = re.sub(r'(?<!\\)\\(?![\\"/bfnrtu])', r"\\\\", value)
            try:
                json.loads(fixed_value)
                return fixed_value
            except json.JSONDecodeError:
                raise serializers.ValidationError("Parameters must be a valid JSON string.")


class RuleResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationRule
        fields = [
            "id",
            "name",
            "dataset_type",
            "field_name",
            "rule_type",
            "parameters",
            "severity",
            "is_active",
            "created_at",
        ]


class RuleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ValidationRule
        fields = ["name", "dataset_type", "field_name", "rule_type", "parameters", "severity", "is_active"]
        extra_kwargs = {
            "name": {"required": False},
            "dataset_type": {"required": False, "allow_blank": True},
            "field_name": {"required": False},
            "rule_type": {"required": False},
            "parameters": {"required": False, "allow_blank": True},
            "severity": {"required": False},
            "is_active": {"required": False},
        }

    def validate_parameters(self, value):
        if not value or not str(value).strip():
            return value
        import json
        import re

        try:
            json.loads(value)
            return value
        except json.JSONDecodeError:
            # Auto-fix unescaped backslashes often sent by Swagger for regex rules
            fixed_value = re.sub(r'(?<!\\)\\(?![\\"/bfnrtu])', r"\\\\", value)
            try:
                json.loads(fixed_value)
                return fixed_value
            except json.JSONDecodeError:
                raise serializers.ValidationError("Parameters must be a valid JSON string.")
