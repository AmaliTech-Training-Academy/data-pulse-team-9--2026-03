from django.contrib import admin

from .models import ValidationRule


@admin.register(ValidationRule)
class ValidationRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "dataset_type", "field_name", "rule_type", "severity", "is_active")
    list_filter = ("dataset_type", "rule_type", "severity", "is_active")
    search_fields = ("name", "field_name")
    ordering = ("-created_at",)
