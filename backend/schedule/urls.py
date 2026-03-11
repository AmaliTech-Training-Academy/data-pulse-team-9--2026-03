from django.urls import path
from schedule.views import AlertConfigView, ScheduleCreateView, ScheduleDetailView, ScheduleToggleView

urlpatterns = [
    path("", ScheduleCreateView.as_view(), name="schedule-create"),
    path("<int:pk>/", ScheduleDetailView.as_view(), name="schedule-detail"),
    path("<int:pk>/<str:action>/", ScheduleToggleView.as_view(), name="schedule-toggle"),
    path("alerts/<int:dataset_id>/", AlertConfigView.as_view(), name="alert-threshold"),
]
