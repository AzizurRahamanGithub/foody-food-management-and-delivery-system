from rest_framework import serializers
from .models import ChatMessage
from django.conf import settings
from django.contrib.auth import get_user_model


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set the model in the __init__ method
        if self.Meta.model is None:
            self.Meta.model = get_user_model()
            self.Meta.fields = ["id", "first_name",
                "last_name", "username", "email", "photo"]


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = serializers.PrimaryKeyRelatedField(read_only=True)
    receiver = serializers.PrimaryKeyRelatedField(read_only=True)
    sender_username = serializers.SerializerMethodField()
    sender_photo = serializers.SerializerMethodField()
    receiver_username = serializers.SerializerMethodField()
    receiver_photo = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = ["id", "sender", "receiver", "sender_username", "receiver_username",
            "sender_photo", "receiver_photo", "message", "timestamp", "is_read"]

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
        fields = ["id", "first_name", "last_name", "photo",  "username",  "all_messages_read", "total_unread_messages"]

    def get_all_messages_read(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return True  # default

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
