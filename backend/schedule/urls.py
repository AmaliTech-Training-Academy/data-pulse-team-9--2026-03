from django.urls import path
from schedule.views import ScheduleCreateView, ScheduleDetailView, ScheduleToggleView

urlpatterns = [
    path("", ScheduleCreateView.as_view(), name="schedule-create"),
    path("<int:pk>/", ScheduleDetailView.as_view(), name="schedule-detail"),
    path("<int:pk>/<str:action>/", ScheduleToggleView.as_view(), name="schedule-toggle"),
]
