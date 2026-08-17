from rest_framework import serializers
from apps.auths.models import CustomUser
from apps.merchant.models import MerchantProfile, MenuItem, Offer, Category, Addon
from apps.merchant.serializers import MenuItemSerializer
from .models import (CustomerProfile, SavedAddress, PaymentMethod,
                     Referral, Wallet, WalletTransaction, Cart, CartItem)


class CustomerProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True, source='user.id')
    email = serializers.EmailField(read_only=True, source='user.email')
    full_name = serializers.CharField(
        read_only=True, source='user.full_name')
    first_name = serializers.CharField(
        source='user.first_name', required=False)
    last_name = serializers.CharField(
        source='user.last_name', required=False)
    phone_number = serializers.CharField(
        source='user.phone_number', required=False)
    wallet_balance = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True)
    referral_code = serializers.CharField(read_only=True)
    referral_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user_id', 'email', 'full_name', 'first_name',
                  'last_name', 'phone_number', 'phone', 'avatar', 'gender',
                  'default_latitude', 'default_longitude',
                  'referral_code', 'referral_count', 'wallet_balance']
        read_only_fields = ['referral_code', 'wallet_balance']

    def get_referral_count(self, obj):
        return obj.referrals_made.count()

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user
        if user_data:
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class SavedAddressSerializer(serializers.ModelSerializer):
    display_label = serializers.CharField(read_only=True)

    class Meta:
        model = SavedAddress
        fields = ['id', 'label', 'custom_label', 'display_label',
                  'address', 'latitude', 'longitude', 'is_default']
        read_only_fields = ['user']

    def validate(self, attrs):
        if attrs.get('label') == 'other' and not attrs.get('custom_label'):
            raise serializers.ValidationError(
                {"custom_label": "Custom label is required when label is 'other'."})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        if validated_data.get('is_default'):
            SavedAddress.objects.filter(user=user).update(is_default=False)
        return SavedAddress.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('is_default'):
            SavedAddress.objects.filter(user=instance.user).update(
                is_default=False)
        return super().update(instance, validated_data)


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'method_type', 'card_holder', 'card_last4',
                  'expiry_month', 'expiry_year', 'is_default']
        read_only_fields = ['user']

    def create(self, validated_data):
        user = self.context['request'].user
        if validated_data.get('is_default'):
            PaymentMethod.objects.filter(user=user).update(is_default=False)
        return PaymentMethod.objects.create(user=user, **validated_data)


class ReferralSerializer(serializers.ModelSerializer):
    referred_email = serializers.EmailField(
        source='referred_user.email', read_only=True)
    referred_name = serializers.CharField(
        source='referred_user.full_name', read_only=True)

    class Meta:
        model = Referral
        fields = ['id', 'referred_user', 'referred_email', 'referred_name',
                  'referral_code_used', 'status', 'reward_amount',
                  'first_order', 'rewarded_at', 'created_at']
        read_only_fields = ['referrer', 'status', 'reward_amount',
                            'first_order', 'rewarded_at', 'created_at']


class ReferralInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists.")
        return value


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance']


class WalletTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WalletTransaction
        fields = ['id', 'transaction_type', 'amount', 'description',
                  'reference', 'created_at']
        read_only_fields = ['created_at']


class CartItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(read_only=True, source='item.name')
    item_image = serializers.CharField(read_only=True, source='item.image')
    item_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2,
        source='unit_price')
    merchant_name = serializers.CharField(
        read_only=True, source='item.merchant.business_name')
    merchant_id = serializers.IntegerField(
        read_only=True, source='item.merchant.id')
    addons = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Addon.objects.all(), required=False)
    addon_details = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_name', 'item_image', 'item_price',
                  'merchant_id', 'merchant_name', 'quantity', 'addons',
                  'addon_details', 'line_total']
        read_only_fields = ['id']

    def get_addon_details(self, obj):
        return [{
            "id": a.id,
            "name": a.name,
            "price": str(a.price),
            "size": a.size,
            "size_display": a.get_size_display() if a.size else None,
            "group_name": a.group.name,
        } for a in obj.addons.all()]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal']

    def get_subtotal(self, obj):
        return round(
            sum(float(i.line_total) for i in obj.items.all()), 2)


class RestaurantCardSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = MerchantProfile
        fields = ['id', 'business_name', 'business_type', 'logo',
                  'cover_photo', 'address', 'city', 'is_open',
                  'delivery_time_min', 'min_order_amount', 'rating',
                  'distance_km']

    def get_rating(self, obj):
        from django.db.models import Avg
        return float(
            obj.reviews.aggregate(avg=Avg('rating'))['avg'] or 0)

    def get_distance_km(self, obj):
        return None


class RestaurantDetailSerializer(RestaurantCardSerializer):
    categories = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    menus = serializers.SerializerMethodField()

    class Meta(RestaurantCardSerializer.Meta):
        fields = RestaurantCardSerializer.Meta.fields + [
            'description', 'manager_phone', 'latitude', 'longitude',
            'categories', 'offers', 'menus']

    def get_categories(self, obj):
        from apps.merchant.serializers import CategorySerializer
        return CategorySerializer(
            obj.menu_categories.all(), many=True).data

    def get_offers(self, obj):
        from apps.merchant.serializers import OfferSerializer
        offers = obj.offers.filter(is_active=True)
        return OfferSerializer(offers, many=True).data

    def get_menus(self, obj):
        items = obj.menu_items.filter(is_available=True)
        return MenuItemSerializer(items, many=True).data
