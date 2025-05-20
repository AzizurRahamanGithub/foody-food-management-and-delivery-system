from django.contrib import admin
from .models import DeliveryZone, PricingRule


@admin.register(DeliveryZone)
class DeliveryZoneAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'area', 'radius_km', 'is_active')
    list_filter = ('is_active',)


@admin.register(PricingRule)
class PricingRuleAdmin(admin.ModelAdmin):
    list_display = ('zone', 'base_fare', 'per_km', 'min_fare', 'is_active')
