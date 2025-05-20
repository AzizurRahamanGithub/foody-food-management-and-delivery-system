import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'
        PREPARING = 'preparing', 'Preparing'
        READY = 'ready', 'Ready for Pickup'
        PICKED_UP = 'picked_up', 'Picked Up'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        CASH_ON_DELIVERY = 'cod', 'Cash on Delivery'
        CARD = 'card', 'Card'
        WALLET = 'wallet', 'Wallet'

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    order_number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='orders')
    merchant = models.ForeignKey(
        'merchant.MerchantProfile', on_delete=models.CASCADE,
        related_name='orders')
    rider = models.ForeignKey(
        'rider.RiderProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders')
    offer = models.ForeignKey(
        'merchant.Offer', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='orders')

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_method = models.CharField(
        max_length=10, choices=PaymentMethod.choices,
        default=PaymentMethod.CASH_ON_DELIVERY)
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING)
    payment_reference = models.CharField(max_length=100, null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    delivery_address = models.CharField(max_length=255, null=True, blank=True)
    delivery_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    note = models.TextField(null=True, blank=True)

    is_scheduled = models.BooleanField(default=False)
    schedule_at = models.DateTimeField(null=True, blank=True)
    estimated_delivery_min = models.PositiveIntegerField(default=30)

    placed_at = models.DateTimeField(default=timezone.now)
    accepted_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancel_reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.order_number} - {self.get_status_display()}"

    @classmethod
    def generate_order_number(cls):
        today = timezone.now().strftime('%Y%m%d')
        count = cls.objects.filter(order_number__startswith=f'TP-{today}').count() + 1
        return f"TP-{today}-{count:04d}"

    def add_status_log(self, status, changed_by=None, note=None):
        OrderStatusLog.objects.create(
            order=self, status=status, changed_by=changed_by, note=note)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(
        'merchant.MenuItem', on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=200)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    addon_text = models.CharField(max_length=500, null=True, blank=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.item_name} x{self.quantity}"


class OrderStatusLog(models.Model):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name='status_logs')
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.order.order_number} -> {self.status}"


class DeliveryTask(TimeStampedModel):
    class Status(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        ACCEPTED = 'accepted', 'Accepted'
        PICKED_UP = 'picked_up', 'Picked Up'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='delivery_task')
    rider = models.ForeignKey(
        'rider.RiderProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='delivery_tasks')
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    pickup_code = models.CharField(max_length=10, null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"Task {self.order.order_number} - {self.get_status_display()}"


class Review(TimeStampedModel):
    order = models.OneToOneField(
        Order, on_delete=models.CASCADE, related_name='review')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reviews')
    merchant = models.ForeignKey(
        'merchant.MerchantProfile', on_delete=models.CASCADE,
        related_name='reviews')
    rider = models.ForeignKey(
        'rider.RiderProfile', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviews')
    rating = models.PositiveSmallIntegerField(default=5)
    rider_rating = models.PositiveSmallIntegerField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"Review for {self.order.order_number}"
