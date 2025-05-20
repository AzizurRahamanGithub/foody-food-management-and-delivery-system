from rest_framework import serializers
from apps.auths.models import CustomUser
from .models import RiderProfile, RiderDocument, BankInfo, Earning


class RiderProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True, source='user.id')
    email = serializers.EmailField(read_only=True, source='user.email')
    full_name = serializers.CharField(read_only=True, source='user.full_name')
    verification_status = serializers.CharField(read_only=True)
    onboarding_complete = serializers.SerializerMethodField()

    class Meta:
        model = RiderProfile
        fields = [
            'id', 'user_id', 'email', 'full_name', 'phone', 'avatar', 'city',
            'preferred_city', 'language', 'availability_status',
            'vehicle_type', 'vehicle_model', 'vehicle_number',
            'current_latitude', 'current_longitude', 'verification_status',
            'is_online', 'onboarding_complete', 'created_at',
        ]

    def get_onboarding_complete(self, obj):
        return all([
            obj.city, obj.vehicle_type, obj.documents.exists(),
        ])


class RiderDocumentSerializer(serializers.ModelSerializer):
    rider = serializers.IntegerField(read_only=True, source='rider.id')

    class Meta:
        model = RiderDocument
        fields = ['id', 'rider', 'doc_type', 'file', 'status',
                  'rejection_reason', 'created_at']
        read_only_fields = ['status', 'rejection_reason']


class BankInfoSerializer(serializers.ModelSerializer):
    user = serializers.IntegerField(read_only=True, source='user.id')

    class Meta:
        model = BankInfo
        fields = ['id', 'user', 'bank_name', 'account_holder',
                  'account_number', 'branch', 'is_verified']
        read_only_fields = ['is_verified']


class EarningSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(
        read_only=True, source='order.order_number')

    class Meta:
        model = Earning
        fields = ['id', 'rider', 'order', 'order_number', 'earning_type',
                  'amount', 'description', 'created_at']
