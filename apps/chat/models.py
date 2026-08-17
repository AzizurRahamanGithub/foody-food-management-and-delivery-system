
from django.db import models
from django.conf import settings


class SupportTicket(models.Model):
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='support_tickets')
    subject = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(
        max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='assigned_tickets')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject}"


class ChatMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="sent_messages",
        on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="received_messages",
        on_delete=models.CASCADE)
    ticket = models.ForeignKey(
        SupportTicket, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender} → {self.receiver}: {self.message[:20]}"
