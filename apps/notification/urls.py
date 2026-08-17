from django.urls import path
from .views import (NotificationListView,
                    NotificationUnreadCountView,
                    NotificationMarkReadView,
                    MarkAllNotificationsReadView)

urlpatterns = [
    path('list/', NotificationListView.as_view(),
         name='notifications'),
    path('unread-count/', NotificationUnreadCountView.as_view(),
         name='notification-unread-count'),
    path('<int:pk>/read/', NotificationMarkReadView.as_view(),
         name='notification-mark-read'),
    path('mark-all-read/', MarkAllNotificationsReadView.as_view(),
         name='mark-all-read'),
]
