from rest_framework import serializers
from apps.auths.models import CustomUser
from apps.merchant.models import MerchantProfile, MenuItem, Offer, Category, Addon
from apps.merchant.serializers import MenuItemSerializer
from .models import CustomerProfile, SavedAddress, PaymentMethod, Cart, CartItem


class CustomerProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True, source='user.id')
    email = serializers.EmailField(read_only=True, source='user.email')
    full_name = serializers.CharField(
        read_only=True, source='user.full_name')

    class Meta:
        model = CustomerProfile
        fields = ['id', 'user_id', 'email', 'full_name', 'phone', 'avatar',
                  'default_latitude', 'default_longitude']


class SavedAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedAddress
        fields = ['id', 'label', 'address', 'latitude',
                  'longitude', 'is_default']
        read_only_fields = ['user']

    def create(self, validated_data):
        user = self.context['request'].user
        if validated_data.get('is_default'):
            SavedAddress.objects.filter(user=user).update(is_default=False)
        return SavedAddress.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        if validated_data.get('is_default'):
            SavedAddress.objects.filter(user=instance.user).update(is_default=False)
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


class CartItemSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(read_only=True, source='item.name')
    item_image = serializers.CharField(read_only=True, source='item.image')
    item_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2, source='unit_price')
    merchant_name = serializers.CharField(
        read_only=True, source='item.merchant.business_name')
    merchant_id = serializers.IntegerField(
        read_only=True, source='item.merchant.id')
    addons = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Addon.objects.all(), required=False)
    addon_names = serializers.SerializerMethodField()
    line_total = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = CartItem
        fields = ['id', 'item', 'item_name', 'item_image', 'item_price',
                  'merchant_id', 'merchant_name', 'quantity', 'addons',
                  'addon_names', 'line_total']
        read_only_fields = ['id']

    def get_addon_names(self, obj):
        return list(obj.addons.values_list('name', flat=True))


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'subtotal']

    def get_subtotal(self, obj):
        return round(sum(float(i.line_total) for i in obj.items.all()), 2)


class RestaurantCardSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField()
    distance_km = serializers.SerializerMethodField()

    class Meta:
        model = MerchantProfile
        fields = ['id', 'business_name', 'business_type', 'logo', 'cover_photo',
                  'address', 'city', 'is_open', 'delivery_time_min',
                  'min_order_amount', 'rating', 'distance_km']

    def get_rating(self, obj):
        from django.db.models import Avg
        return float(obj.reviews.aggregate(avg=Avg('rating'))['avg'] or 0)

    def get_distance_km(self, obj):
        return None


class RestaurantDetailSerializer(RestaurantCardSerializer):
    categories = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    menus = serializers.SerializerMethodField()

    class Meta(RestaurantCardSerializer.Meta):
        fields = RestaurantCardSerializer.Meta.fields + [
            'description', 'phone', 'opening_time', 'closing_time',
            'latitude', 'longitude', 'categories', 'offers', 'menus']

    def get_categories(self, obj):
        from apps.merchant.serializers import CategorySerializer
        return CategorySerializer(obj.categories.all(), many=True).data

    def get_offers(self, obj):
        from apps.merchant.serializers import OfferSerializer
        offers = obj.offers.filter(is_active=True)
        return OfferSerializer(offers, many=True).data

    def get_menus(self, obj):
        items = obj.menu_items.filter(is_available=True)
        return MenuItemSerializer(items, many=True).data
