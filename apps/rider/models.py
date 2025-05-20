from django.db import models
from django.conf import settings
from apps.core.models import TimeStampedModel


class RiderProfile(TimeStampedModel):
    class Availability(models.TextChoices):
        ONLINE = 'online', 'Online'
        OFFLINE = 'offline', 'Offline'

    class VehicleType(models.TextChoices):
        BIKE = 'bike', 'Bike'
        CAR = 'car', 'Car'
        BICYCLE = 'bicycle', 'Bicycle'

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='rider_profile')
    phone = models.CharField(max_length=20, null=True, blank=True)
    avatar = models.URLField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    preferred_city = models.CharField(max_length=100, null=True, blank=True)
    language = models.CharField(max_length=50, null=True, blank=True)
    availability_status = models.CharField(
        max_length=10, choices=Availability.choices,
        default=Availability.OFFLINE)
    vehicle_type = models.CharField(
        max_length=10, choices=VehicleType.choices, null=True, blank=True)
    vehicle_model = models.CharField(max_length=100, null=True, blank=True)
    vehicle_number = models.CharField(max_length=50, null=True, blank=True)
    current_latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    verification_status = models.CharField(
        max_length=20, choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        return f"Rider {self.user.email}"

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.APPROVED


class RiderDocument(TimeStampedModel):
    class DocType(models.TextChoices):
        NATIONAL_ID = 'national_id', 'National ID'
        DRIVING_LICENSE = 'driving_license', 'Driving License'
        VEHICLE_REG = 'vehicle_reg', 'Vehicle Registration'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'

    rider = models.ForeignKey(
        RiderProfile, on_delete=models.CASCADE, related_name='documents')
    doc_type = models.CharField(max_length=20, choices=DocType.choices)
    file = models.URLField()
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PENDING)
    rejection_reason = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.rider.user.email} - {self.get_doc_type_display()}"


class BankInfo(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bank_infos')
    bank_name = models.CharField(max_length=200)
    account_holder = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100)
    branch = models.CharField(max_length=200, null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.user.email} - {self.bank_name}"


class Earning(TimeStampedModel):
    class EarningType(models.TextChoices):
        DELIVERY_FEE = 'delivery_fee', 'Delivery Fee'
        TIP = 'tip', 'Tip'
        BONUS = 'bonus', 'Bonus'
        PENALTY = 'penalty', 'Penalty'

    rider = models.ForeignKey(
        RiderProfile, on_delete=models.CASCADE, related_name='earnings')
    order = models.ForeignKey(
        'orders.Order', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='rider_earnings')
    earning_type = models.CharField(
        max_length=20, choices=EarningType.choices,
        default=EarningType.DELIVERY_FEE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.rider.user.email} - {self.amount}"
