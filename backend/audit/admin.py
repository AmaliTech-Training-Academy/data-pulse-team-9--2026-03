from audit.models import AuditLog
from django.contrib import admin


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("dataset", "triggered_by", "trigger_type", "score", "timestamp")
    list_filter = ("trigger_type", "timestamp", "dataset")
    search_fields = ("triggered_by", "dataset__name")

    def has_add_permission(self, request):
        # Only system/service should add, but we can allow admin add if needed
        # Requirement says "no delete or update operations are exposed"
        return True

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
