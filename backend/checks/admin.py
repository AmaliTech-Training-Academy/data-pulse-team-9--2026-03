from django.contrib import admin
from .models import CheckResult, QualityScore

@admin.register(CheckResult)
class CheckResultAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'rule', 'passed', 'failed_rows', 'total_rows', 'checked_at')
    list_filter = ('passed', 'rule__rule_type')
    search_fields = ('dataset__name', 'rule__name')
    ordering = ('-checked_at',)

@admin.register(QualityScore)
class QualityScoreAdmin(admin.ModelAdmin):
    list_display = ('dataset', 'score', 'passed_rules', 'failed_rules', 'checked_at')
    list_filter = ('score',)
    search_fields = ('dataset__name',)
    ordering = ('-checked_at',)
