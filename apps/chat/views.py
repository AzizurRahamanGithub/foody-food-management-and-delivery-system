from ..core.response import success_response, failure_response
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import ChatMessage
from .serializers import ChatMessageSerializer, UserSerializer, ChatUserSerializer

User = get_user_model()


# CRUD for ChatMessage
class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all().order_by("timestamp")
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


# Chat history with another user
class ChatMessageListView(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        other_user_id = self.kwargs["user_id"]
        return ChatMessage.objects.filter(
            Q(sender=user, receiver_id=other_user_id) |
            Q(sender_id=other_user_id, receiver=user)
        ).order_by("-timestamp")
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response("Chat history fetched successfully", serializer.data)


# Mark all unread messages as read for current user
class IsReadMessageView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        unread_messages = ChatMessage.objects.filter(
            receiver=user, is_read=False)
        count = unread_messages.update(is_read=True)
        return Response({
            "success": True,
            "message": f"{count} messages marked as read."
        }, status=status.HTTP_200_OK)


# List of users the current user has chatted with

class MyChatUserListView(generics.ListAPIView):
    serializer_class = ChatUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        chat_user_ids = ChatMessage.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values_list('sender', 'receiver')

        user_ids = set()
        for sender_id, receiver_id in chat_user_ids:
            if sender_id != user.id:
                user_ids.add(sender_id)
            if receiver_id != user.id:
                user_ids.add(receiver_id)

        return User.objects.filter(id__in=user_ids)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return success_response(
            message="Chat users fetched successfully",
            data=serializer.data
        )
