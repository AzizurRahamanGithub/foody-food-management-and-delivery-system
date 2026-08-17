from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (ChatMessageViewSet, ChatMessageListView,
                    IsReadMessageView, MyChatUserListView,
                    SupportTicketView, SupportTicketDetailView,
                    SupportTicketMessagesView)

router = DefaultRouter()
router.register(r"messages", ChatMessageViewSet, basename="chatmessage")

urlpatterns = [
    path("read/all-message/", IsReadMessageView.as_view(),
         name="mark-messages-read"),

    path("support/tickets/", SupportTicketView.as_view(),
         name="support-tickets"),
    path("support/tickets/<int:pk>/", SupportTicketDetailView.as_view(),
         name="support-ticket-detail"),
    path("support/tickets/<int:pk>/messages/",
         SupportTicketMessagesView.as_view(),
         name="support-ticket-messages"),

    path("", include(router.urls)),
    path("history/<int:user_id>/", ChatMessageListView.as_view(),
         name="chat-history"),
    path("my/list/", MyChatUserListView.as_view(),
         name="my-chat-users"),
]
