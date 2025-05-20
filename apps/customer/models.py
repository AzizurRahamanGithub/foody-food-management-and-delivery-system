from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class CustomerProfile(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='customer_profile')
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.URLField(null=True, blank=True)
    default_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    default_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    def __str__(self):
        return f"Customer {self.user.email}"


class SavedAddress(TimeStampedModel):
    class Label(models.TextChoices):
        HOME = 'home', 'Home'
        WORK = 'work', 'Work'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='saved_addresses')
    label = models.CharField(
        max_length=10, choices=Label.choices, default=Label.HOME)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.user.email} - {self.address}"


class PaymentMethod(TimeStampedModel):
    class MethodType(models.TextChoices):
        CASH_ON_DELIVERY = 'cod', 'Cash on Delivery'
        CARD = 'card', 'Card'
        WALLET = 'wallet', 'Wallet'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='payment_methods')
    method_type = models.CharField(
        max_length=10, choices=MethodType.choices,
        default=MethodType.CASH_ON_DELIVERY)
    card_holder = models.CharField(max_length=200, null=True, blank=True)
    card_last4 = models.CharField(max_length=4, null=True, blank=True)
    expiry_month = models.CharField(max_length=2, null=True, blank=True)
    expiry_year = models.CharField(max_length=4, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.user.email} - {self.get_method_type_display()}"


class Cart(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='cart')

    def __str__(self):
        return f"Cart of {self.user.email}"


class CartItem(TimeStampedModel):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(
        'merchant.MenuItem', on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)
    addons = models.ManyToManyField('merchant.Addon', blank=True)

    class Meta:
        unique_together = ('cart', 'item')

    def __str__(self):
        return f"{self.item.name} x{self.quantity}"

    @property
    def unit_price(self):
        return self.item.effective_price

    @property
    def addon_total(self):
        return sum(float(a.price) for a in self.addons.all())

    @property
    def line_total(self):
        return round((float(self.unit_price) + self.addon_total) * self.quantity, 2)
