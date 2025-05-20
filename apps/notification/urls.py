from django.urls import path
from .views import NotificationListView, MarkAllNotificationsReadView

urlpatterns = [
    path("list/", NotificationListView.as_view(), name="notifications"),
    path("mark-all-read/", MarkAllNotificationsReadView.as_view(), name="mark-all-read"),
]
