from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    time_ago = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'notification_type', 'title', 'message',
                  'data', 'image', 'is_read', 'time_ago',
                  'created_at']

    def get_time_ago(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            m = seconds // 60
            return f"{m}m ago"
        if seconds < 86400:
            h = seconds // 3600
            return f"{h}h ago"
        d = seconds // 86400
        return f"{d}d ago"


class NotificationSummarySerializer(serializers.Serializer):
    total = serializers.IntegerField()
    unread = serializers.IntegerField()
    read = serializers.IntegerField()
