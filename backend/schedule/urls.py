from django.urls import path
from schedule.views import ScheduleCreateView

urlpatterns = [
    path("", ScheduleCreateView.as_view(), name="schedule-create"),
]
