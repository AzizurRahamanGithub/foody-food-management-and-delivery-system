from ..core.response import success_response, failure_response
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import SupportTicket, ChatMessage
from .serializers import (ChatMessageSerializer, UserSerializer,
                          ChatUserSerializer, SupportTicketSerializer,
                          SupportTicketCreateSerializer)


User = get_user_model()


class SupportTicketView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        tickets = SupportTicket.objects.filter(user=request.user)
        status_filter = request.query_params.get('status')
        if status_filter:
            tickets = tickets.filter(status=status_filter)
        return success_response(
            "Support tickets",
            SupportTicketSerializer(tickets, many=True).data)

    def post(self, request):
        serializer = SupportTicketCreateSerializer(
            data=request.data, context={'request': request})
        if serializer.is_valid():
            ticket = serializer.save()
            return success_response(
                "Support ticket created",
                SupportTicketSerializer(ticket).data,
                status.HTTP_201_CREATED)
        return failure_response("Invalid data", serializer.errors)


class SupportTicketDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        ticket = get_object_or_404(
            SupportTicket, pk=pk, user=request.user)
        return success_response(
            "Ticket details",
            SupportTicketSerializer(ticket).data)


class SupportTicketMessagesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        ticket = get_object_or_404(
            SupportTicket, pk=pk, user=request.user)
        messages = ticket.messages.order_by('timestamp')
        return success_response(
            "Ticket messages",
            ChatMessageSerializer(messages, many=True).data)

    def post(self, request, pk):
        ticket = get_object_or_404(
            SupportTicket, pk=pk, user=request.user)
        if ticket.status == 'closed':
            return failure_response("Ticket is closed")
        message_text = request.data.get('message')
        if not message_text:
            return failure_response("Message is required")
        receiver = ticket.assigned_to or User.objects.filter(
            is_staff=True).first()
        if not receiver:
            return failure_response("No support staff available")
        msg = ChatMessage.objects.create(
            sender=request.user,
            receiver=receiver,
            ticket=ticket,
            message=message_text)
        return success_response(
            "Message sent",
            ChatMessageSerializer(msg).data,
            status.HTTP_201_CREATED)


# --- Existing views below ---

class ChatMessageViewSet(viewsets.ModelViewSet):
    queryset = ChatMessage.objects.all().order_by("timestamp")
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)


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
        return success_response(
            "Chat history fetched successfully", serializer.data)


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
