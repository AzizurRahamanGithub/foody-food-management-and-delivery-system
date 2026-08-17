from django.contrib import admin
from .models import SupportTicket, ChatMessage


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subject', 'status', 'priority',
                    'assigned_to', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('subject', 'user__email', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'ticket', 'message',
                    'timestamp', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('sender__email', 'receiver__email', 'message')
