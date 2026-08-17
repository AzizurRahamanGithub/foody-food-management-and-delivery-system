from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order_placed', 'Order Placed'),
        ('order_confirmed', 'Order Confirmed'),
        ('order_preparing', 'Order Preparing'),
        ('order_out_for_delivery', 'Out for Delivery'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('rate_order', 'Rate Your Order'),
        ('promotion', 'Promotion'),
        ('deal', 'Deal'),
        ('payment', 'Payment'),
        ('general', 'General'),
    ]

    user = models.ForeignKey(
        User, related_name='notifications',
        on_delete=models.CASCADE)
    notification_type = models.CharField(
        max_length=30, choices=NOTIFICATION_TYPES,
        default='general')
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=500)
    data = models.JSONField(
        default=dict, blank=True,
        help_text='Extra data: order_id, promo_code, merchant_name, etc.')
    image = models.URLField(blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.title}"

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
        return {
            "read": cls.read_count(user),
            "unread": cls.unread_count(user),
            "total": cls.total_count(user),
        }

    @classmethod
    def create_for_user(cls, user, notification_type, title,
                        message, data=None, image=None):
        return cls.objects.create(
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            data=data or {},
            image=image)
