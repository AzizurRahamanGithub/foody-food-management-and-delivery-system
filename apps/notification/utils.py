from django.contrib.auth import get_user_model
from .models import Notification
from apps.auths.models import Role  # adjust import if Role is in another app

User = get_user_model()

def notify_admins(title, message):
    """Create a notification for all users with role='admin'."""
    admin_users = User.objects.filter(role=Role.ADMIN, is_active=True)
    for admin in admin_users:
        Notification.objects.create(
            user=admin,
            title=title,
            message=message
        )
