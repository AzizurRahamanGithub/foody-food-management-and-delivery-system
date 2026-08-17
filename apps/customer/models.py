import string
import random
from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


def generate_referral_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


class CustomerProfile(TimeStampedModel):
    class Gender(models.TextChoices):
        MALE = 'male', 'Male'
        FEMALE = 'female', 'Female'
        OTHER = 'other', 'Other'
        PREFER_NOT_TO_SAY = 'prefer_not_to_say', 'Prefer not to say'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='customer_profile')
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.URLField(null=True, blank=True)
    gender = models.CharField(
        max_length=20, choices=Gender.choices,
        default=Gender.PREFER_NOT_TO_SAY)
    default_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    default_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    referral_code = models.CharField(
        max_length=8, unique=True, default=generate_referral_code)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='referrals_made')

    def __str__(self):
        return f"Customer {self.user.email}"

    @property
    def wallet_balance(self):
        wallet, _ = Wallet.objects.get_or_create(user=self.user)
        return wallet.balance


class SavedAddress(TimeStampedModel):
    class Label(models.TextChoices):
        HOME = 'home', 'Home'
        WORK = 'work', 'Work'
        OTHER = 'other', 'Other'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='saved_addresses')
    label = models.CharField(
        max_length=50, choices=Label.choices, default=Label.HOME)
    custom_label = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', '-id']

    def __str__(self):
        label = self.custom_label or self.get_label_display()
        return f"{self.user.email} - {label}: {self.address}"

    @property
    def display_label(self):
        return self.custom_label if self.label == 'other' and self.custom_label else self.get_label_display()


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


class Referral(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        EARNED = 'earned', 'Earned'
        EXPIRED = 'expired', 'Expired'

    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='referrals_given')
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='referral_received')
    referral_code_used = models.CharField(max_length=8)
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING)
    reward_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=1000)
    first_order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='triggered_referral')
    rewarded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.referrer.email} → {self.referred_user.email} ({self.status})"


class Wallet(TimeStampedModel):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Wallet - {self.user.email}: ₦{self.balance}"


class WalletTransaction(TimeStampedModel):
    class Type(models.TextChoices):
        CREDIT = 'credit', 'Credit'
        DEBIT = 'debit', 'Debit'

    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(
        max_length=10, choices=Type.choices)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type}: ₦{self.amount} - {self.description}"


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
        'merchant.MenuItem', on_delete=models.CASCADE,
        related_name='cart_items')
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
        return round(
            (float(self.unit_price) + self.addon_total) * self.quantity, 2)


class FavoriteItem(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='favorite_items')
    item = models.ForeignKey(
        'merchant.MenuItem', on_delete=models.CASCADE,
        related_name='favorited_by')

    class Meta:
        unique_together = ('user', 'item')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} ❤ {self.item.name}"


class RecentSearch(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='recent_searches')
    query = models.CharField(max_length=255)
    search_type = models.CharField(
        max_length=20,
        choices=[('food', 'Food'), ('store', 'Store'), ('general', 'General')],
        default='general')
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} — {self.query}"
