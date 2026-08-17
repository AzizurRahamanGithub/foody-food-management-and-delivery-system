from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel


class GlobalCategory(TimeStampedModel):
    name = models.CharField(max_length=100, unique=True)
    image = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Global Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


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

    manager_name = models.CharField(max_length=255, null=True, blank=True)
    manager_email = models.EmailField(null=True, blank=True)
    manager_phone = models.CharField(max_length=20, null=True, blank=True)

    address = models.CharField(max_length=255, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)

    shop_no = models.CharField(max_length=50, null=True, blank=True)
    floor_name = models.CharField(max_length=100, null=True, blank=True)
    building_name = models.CharField(max_length=150, null=True, blank=True)
    nearby_landmark = models.CharField(max_length=255, null=True, blank=True)
    additional_direction = models.TextField(null=True, blank=True)

    is_open = models.BooleanField(default=False)
    delivery_time_min = models.PositiveIntegerField(default=30)
    min_order_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)

    categories = models.ManyToManyField(
        GlobalCategory, blank=True, related_name='merchants')

    general_notification_on = models.BooleanField(default=True)
    payment_notification_on = models.BooleanField(default=True)
    app_update_notification_on = models.BooleanField(default=True)
    language = models.CharField(
        max_length=10, default='en',
        choices=[
            ('en_us', 'English (US)'),
            ('en_uk', 'English (UK)'),
            ('zh', 'Mandarin'),
            ('hi', 'Hindi'),
            ('es', 'Spanish'),
            ('fr', 'French'),
            ('ar', 'Arabic'),
            ('bn', 'Bengali'),
            ('ru', 'Russian'),
            ('id', 'Indonesian'),
        ])

    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING)
    is_featured = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Merchant Profiles'

    def __str__(self):
        return self.business_name or f"Merchant {self.user.email}"

    @property
    def is_profile_setup(self):
        if self.verification_status != 'approved':
            return False
        required_fields = [
            self.business_type, self.business_name, self.address,
            self.city, self.manager_name, self.manager_phone,
        ]
        has_schedule = self.schedules.filter(is_open=True).exists()
        return all(required_fields) and has_schedule


class MerchantSchedule(TimeStampedModel):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    merchant = models.ForeignKey(
        MerchantProfile, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.PositiveSmallIntegerField(choices=DAY_CHOICES)
    is_open = models.BooleanField(default=True)
    opening_time = models.TimeField(null=True, blank=True)
    closing_time = models.TimeField(null=True, blank=True)

    class Meta:
        unique_together = ('merchant', 'day_of_week')
        ordering = ['day_of_week']

    def __str__(self):
        day = self.get_day_of_week_display()
        status = 'Open' if self.is_open else 'Closed'
        return f"{self.merchant.business_name} - {day}: {status}"


class MerchantVerification(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    merchant = models.OneToOneField(
        MerchantProfile, on_delete=models.CASCADE,
        related_name='verification')
    business_name = models.CharField(max_length=255)
    cac_registration_no = models.CharField(max_length=100)
    cac_document = models.URLField()
    account_no = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='reviewed_verifications')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Merchant Verifications'

    def __str__(self):
        return f"Verification - {self.merchant.business_name} ({self.status})"


class Category(TimeStampedModel):
    merchant = models.ForeignKey(
        MerchantProfile, on_delete=models.CASCADE, related_name='menu_categories')
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
    preparation_time_min = models.PositiveIntegerField(
        null=True, blank=True, default=15)
    stock_quantity = models.PositiveIntegerField(null=True, blank=True)
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
        MerchantProfile, on_delete=models.CASCADE,
        related_name='addon_groups')
    name = models.CharField(max_length=100)
    is_required = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=True)
    max_selectable = models.PositiveSmallIntegerField(
        default=0,
        help_text='0 = unlimited, 1 = single choice, 2+ = limited')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.merchant.business_name} — {self.name}"


class Addon(TimeStampedModel):
    SIZE_CHOICES = [
        ('', 'No Size'),
        ('regular', 'Regular'),
        ('large', 'Large'),
        ('xl', 'XL'),
    ]

    group = models.ForeignKey(
        AddonGroup, on_delete=models.CASCADE,
        related_name='addons')
    name = models.CharField(max_length=100)
    price = models.DecimalField(
        max_digits=10, decimal_places=2, default=0)
    size = models.CharField(
        max_length=20, choices=SIZE_CHOICES, blank=True, default='')
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ['size', 'name']

    def __str__(self):
        size_str = f" ({self.get_size_display()})" if self.size else ""
        return f"{self.name}{size_str} +₦{self.price}"


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
    items = models.ManyToManyField(
        MenuItem, blank=True, related_name='offers')
    valid_from = models.DateTimeField(null=True, blank=True)
    valid_to = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.merchant.business_name} - {self.title}"


class ItemReview(TimeStampedModel):
    item = models.ForeignKey(
        MenuItem, on_delete=models.CASCADE, related_name='item_reviews')
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='item_reviews')
    order = models.ForeignKey(
        'orders.Order', on_delete=models.CASCADE,
        related_name='item_reviews', null=True, blank=True)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('item', 'customer', 'order')

    def __str__(self):
        return f"Review for {self.item.name} by {self.customer.email}"
