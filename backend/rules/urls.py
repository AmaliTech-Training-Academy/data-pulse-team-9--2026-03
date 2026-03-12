"""Rules URL configuration."""

from django.urls import path
from rules.views import RuleDetailView, RuleListCreateView

urlpatterns = [
    path("", RuleListCreateView.as_view(), name="rules-root"),
    path("<int:rule_id>", RuleDetailView.as_view(), name="rule-detail"),
]
