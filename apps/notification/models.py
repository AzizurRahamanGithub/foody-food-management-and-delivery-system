from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    user = models.ForeignKey(User, related_name="notifications", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message}"

    @classmethod
    def unread_count(cls, user):
        return cls.objects.filter(user=user, is_read=False).count()

    @classmethod
    def read_count(cls, user):
        return cls.objects.filter(user=user, is_read=True).count()

    @classmethod
    def total_count(cls, user):
        return cls.objects.filter(user=user).count()

    @classmethod
    def get_summary(cls, user):
        """Returns a dict with read, unread, and total counts"""
        return {
            "read": cls.read_count(user),
            "unread": cls.unread_count(user),
            "total": cls.total_count(user),
        }
