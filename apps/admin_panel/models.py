from django.db import models
from apps.core.models import TimeStampedModel


class DeliveryZone(TimeStampedModel):
    name = models.CharField(max_length=150)
    city = models.CharField(max_length=100, null=True, blank=True)
    area = models.CharField(max_length=150, null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(
        max_digits=9, decimal_places=6, null=True, blank=True)
    radius_km = models.DecimalField(max_digits=6, decimal_places=2, default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PricingRule(TimeStampedModel):
    zone = models.ForeignKey(
        DeliveryZone, on_delete=models.CASCADE, related_name='pricing_rules')
    base_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    per_km = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    min_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f"{self.zone.name} - base {self.base_fare}"
