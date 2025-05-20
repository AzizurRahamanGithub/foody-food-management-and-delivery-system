from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatMessageViewSet, ChatMessageListView, IsReadMessageView, MyChatUserListView

router = DefaultRouter()
router.register(r"messages", ChatMessageViewSet, basename="chatmessage")

urlpatterns = [
    # Mark all unread messages as read (put this BEFORE the router)
    path("read/all-message/", IsReadMessageView.as_view(), name="mark-messages-read"),

    # CRUD routes from ViewSet
    path("", include(router.urls)),

    # Chat history with a specific user
    path("history/<int:user_id>/", ChatMessageListView.as_view(), name="chat-history"),

    # List of users the current user has chatted with
    path("my/list/", MyChatUserListView.as_view(), name="my-chat-users"),
]
