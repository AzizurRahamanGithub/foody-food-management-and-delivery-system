from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel


class MerchantProfile(TimeStampedModel):
    class BusinessType(models.TextChoices):
        RESTAURANT = 'restaurant', 'Restaurant'
        STORE = 'store', 'Store'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='merchant_profile')
    business_type = models.CharField(
        max_length=20, choices=BusinessType.choices, null=True, blank=True)
    business_name = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    logo = models.URLField(null=True, blank=True)
    cover_photo = models.URLField(null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    is_open = models.BooleanField(default=False)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)
    delivery_time_min = models.PositiveIntegerField(default=30)
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING)
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.business_name or f"Merchant {self.user.email}"


class Category(TimeStampedModel):
    merchant = models.ForeignKey(
        MerchantProfile, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    image = models.URLField(null=True, blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']
        unique_together = ('merchant', 'name')

    def __str__(self):
        return f"{self.merchant.business_name} - {self.name}"


class MenuItem(TimeStampedModel):
    merchant = models.ForeignKey(
        MerchantProfile, on_delete=models.CASCADE, related_name='menu_items')
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='items')
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    is_available = models.BooleanField(default=True)
    is_veg = models.BooleanField(default=True)
    preparation_time_min = models.PositiveIntegerField(default=15)
    rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.name

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price < self.price:
            return self.discount_price
        return self.price


class AddonGroup(TimeStampedModel):
    merchant = models.ForeignKey(
        MerchantProfile, on_delete=models.CASCADE, related_name='addon_groups')
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Addon(TimeStampedModel):
    group = models.ForeignKey(
        AddonGroup, on_delete=models.CASCADE, related_name='addons')
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.name} (+{self.price})"


class MenuItemAddon(TimeStampedModel):
    item = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, related_name='item_addons')
    group = models.ForeignKey(
        AddonGroup, on_delete=models.CASCADE, related_name='item_groups')

    class Meta:
        unique_together = ('item', 'group')


class Offer(TimeStampedModel):
    class DiscountType(models.TextChoices):
        PERCENT = 'percent', 'Percent'
        FLAT = 'flat', 'Flat'

    merchant = models.ForeignKey(
        MerchantProfile, on_delete=models.CASCADE, related_name='offers')
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    image = models.URLField(null=True, blank=True)
    discount_type = models.CharField(
        max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
    discount_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True)
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.merchant.business_name} - {self.title}"
