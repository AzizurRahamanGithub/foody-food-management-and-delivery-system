from rest_framework import serializers
from apps.auths.models import CustomUser
from .models import DeliveryZone, PricingRule


class DeliveryZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryZone
        fields = ['id', 'name', 'city', 'area', 'latitude', 'longitude',
                  'radius_km', 'is_active']


class PricingRuleSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(
        read_only=True, source='zone.name')

    class Meta:
        model = PricingRule
        fields = ['id', 'zone', 'zone_name', 'base_fare',
                  'per_km', 'min_fare', 'is_active']
