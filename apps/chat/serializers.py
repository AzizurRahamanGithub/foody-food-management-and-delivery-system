from rest_framework import serializers
from .models import SupportTicket, ChatMessage
from django.conf import settings
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.Meta.model is None:
            self.Meta.model = get_user_model()
            self.Meta.fields = ["id", "first_name",
                "last_name", "username", "email", "photo"]


class SupportTicketSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = SupportTicket
        fields = ['id', 'user', 'user_email', 'subject', 'description',
                  'status', 'priority', 'assigned_to', 'message_count',
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ['id', 'subject', 'description', 'priority']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(read_only=True)
    sender_username = serializers.SerializerMethodField()
    sender_photo = serializers.SerializerMethodField()
    receiver_username = serializers.SerializerMethodField()
    receiver_photo = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "receiver", "sender_username",
                  "receiver_username", "sender_photo", "receiver_photo",
                  "message", "ticket", "timestamp", "is_read"]

    def get_sender_username(self, obj):
        return obj.sender.username

    def get_receiver_username(self, obj):
        return obj.receiver.username

    def get_sender_photo(self, obj):
        return obj.sender.photo if obj.sender.photo else None

    def get_receiver_photo(self, obj):
        return obj.receiver.photo if obj.receiver.photo else None


class IsReadMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ["id", "is_read"]


User = get_user_model()


class ChatUserSerializer(serializers.ModelSerializer):
    all_messages_read = serializers.SerializerMethodField()
    total_unread_messages = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "photo",
                  "username", "all_messages_read",
                  "total_unread_messages"]

    def get_all_messages_read(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return True
        return not ChatMessage.objects.filter(
            sender=obj, receiver=request.user, is_read=False
        ).exists()

    def get_total_unread_messages(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        return ChatMessage.objects.filter(
            sender=obj, receiver=request.user, is_read=False
        ).count()
