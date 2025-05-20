# yourapp/context_processors.py
from .models import Notification

def notification_context(request):
    user = getattr(request, "user", None)
    unread_count = 0
    if user and user.is_authenticated:
        unread_count = Notification.objects.filter(user=user, is_read=False).count()
    return {"notification_unread_count": unread_count}

