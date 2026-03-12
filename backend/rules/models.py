"""Validation rule model matching original SQLAlchemy model."""

from django.db import models


class ValidationRule(models.Model):
    """A data validation rule that can be applied to datasets."""

    name = models.CharField(max_length=255)
    dataset_type = models.CharField(max_length=100)
    field_name = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=20)
    parameters = models.TextField(null=True, blank=True)
    severity = models.CharField(max_length=10, default="MEDIUM")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "validation_rules"

    def __str__(self):
        return f"{self.name} ({self.rule_type})"
