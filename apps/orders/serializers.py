from rest_framework import serializers
from apps.auths.models import CustomUser
from apps.merchant.models import MerchantProfile
from apps.rider.models import RiderProfile
from .models import Order, OrderItem, OrderStatusLog, DeliveryTask, Review


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['id', 'item', 'item_name', 'item_price',
                  'quantity', 'addon_text', 'total']


class OrderStatusLogSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(
        read_only=True, source='changed_by.full_name')

    class Meta:
        model = OrderStatusLog
        fields = ['id', 'status', 'note', 'created_at', 'changed_by_name']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'order', 'rating', 'rider_rating', 'comment', 'created_at']
        read_only_fields = ['order']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(read_only=True, source='get_status_display')
    payment_method_display = serializers.CharField(
        read_only=True, source='get_payment_method_display')
    customer_name = serializers.CharField(read_only=True, source='customer.full_name')
    customer_phone = serializers.CharField(
        read_only=True, source='customer.phone_number')
    merchant_name = serializers.CharField(
        read_only=True, source='merchant.business_name')
    merchant_address = serializers.CharField(
        read_only=True, source='merchant.address')
    rider_name = serializers.SerializerMethodField()
    rider_phone = serializers.SerializerMethodField()
    review = ReviewSerializer(read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'status_display',
            'payment_method', 'payment_method_display', 'payment_status',
            'customer_name', 'customer_phone', 'merchant', 'merchant_name',
            'merchant_address', 'rider', 'rider_name', 'rider_phone',
            'subtotal', 'delivery_fee', 'discount', 'service_fee', 'total',
            'delivery_address', 'delivery_latitude', 'delivery_longitude',
            'note', 'is_scheduled', 'schedule_at', 'estimated_delivery_min',
            'placed_at', 'accepted_at', 'delivered_at', 'items',
            'status_logs', 'review',
        ]

    def get_rider_name(self, obj):
        if obj.rider:
            return obj.rider.user.full_name or obj.rider.user.email
        return None

    def get_rider_phone(self, obj):
        return obj.rider.phone if obj.rider else None


class OrderCreateItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    addon_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list)


class OrderCreateSerializer(serializers.Serializer):
    merchant_id = serializers.IntegerField()
    items = OrderCreateItemSerializer(many=True, required=False)
    delivery_address = serializers.CharField()
    delivery_latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False)
    delivery_longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False)
    payment_method = serializers.ChoiceField(
        choices=Order.PaymentMethod.choices, default='cod')
    offer_id = serializers.IntegerField(required=False)
    note = serializers.CharField(required=False, allow_blank=True)
    is_scheduled = serializers.BooleanField(default=False)
    schedule_at = serializers.DateTimeField(required=False)


class DeliveryTaskSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = DeliveryTask
        fields = ['id', 'order', 'order_id', 'rider', 'status',
                  'pickup_code', 'picked_up_at', 'delivered_at', 'created_at']
        read_only_fields = ['rider', 'pickup_code', 'picked_up_at', 'delivered_at']
