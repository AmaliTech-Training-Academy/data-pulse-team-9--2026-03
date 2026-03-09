"""Check result models matching original SQLAlchemy models."""

from django.db import models


class CheckResult(models.Model):
    """Result of running a validation rule against a dataset."""

    dataset = models.ForeignKey("datasets.Dataset", on_delete=models.CASCADE)
    rule = models.ForeignKey("rules.ValidationRule", on_delete=models.CASCADE)
    passed = models.BooleanField()
    failed_rows = models.IntegerField(default=0)
    total_rows = models.IntegerField(default=0)
    details = models.TextField(null=True, blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "check_results"


class QualityScore(models.Model):
    """Aggregate quality score for a dataset check run."""

    dataset = models.ForeignKey("datasets.Dataset", on_delete=models.CASCADE)
    score = models.FloatField()
    total_rules = models.IntegerField(default=0)
    passed_rules = models.IntegerField(default=0)
    failed_rules = models.IntegerField(default=0)
    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "quality_scores"
