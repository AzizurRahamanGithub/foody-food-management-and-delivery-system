from rest_framework import serializers
from apps.auths.models import CustomUser
from .models import (MerchantProfile, Category, MenuItem,
                     AddonGroup, Addon, MenuItemAddon, Offer)


class MerchantProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True, source='user.id')
    email = serializers.EmailField(read_only=True, source='user.email')
    business_type = serializers.ChoiceField(
        choices=MerchantProfile.BusinessType.choices, required=False)
    verification_status = serializers.CharField(read_only=True)
    onboarding_complete = serializers.SerializerMethodField()

    class Meta:
        model = MerchantProfile
        fields = [
            'id', 'user_id', 'email', 'business_type', 'business_name',
            'description', 'logo', 'cover_photo', 'phone', 'address', 'city',
            'latitude', 'longitude', 'is_open', 'opening_time', 'closing_time',
            'delivery_time_min', 'min_order_amount', 'verification_status',
            'is_featured', 'onboarding_complete', 'created_at',
        ]
        read_only_fields = ['verification_status', 'is_featured', 'created_at']

    def get_onboarding_complete(self, obj):
        return all([
            obj.business_type, obj.business_name, obj.address,
            obj.opening_time, obj.closing_time,
        ])


class AddonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Addon
        fields = ['id', 'name', 'price']


class AddonGroupSerializer(serializers.ModelSerializer):
    addons = AddonSerializer(many=True, read_only=True)

    class Meta:
        model = AddonGroup
        fields = ['id', 'merchant', 'name', 'is_required',
                  'is_multiple_choice', 'addons']
        read_only_fields = ['merchant']


class CategorySerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'merchant', 'name', 'image', 'sort_order', 'item_count']
        read_only_fields = ['merchant']

    def get_item_count(self, obj):
        return obj.items.count()


class MenuItemSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        read_only=True, source='category.name')
    effective_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = MenuItem
        fields = [
            'id', 'merchant', 'category', 'category_name', 'name',
            'description', 'price', 'discount_price', 'effective_price',
            'image', 'is_available', 'is_veg', 'preparation_time_min',
            'rating',
        ]
        read_only_fields = ['merchant']


class MenuItemDetailSerializer(MenuItemSerializer):
    addon_groups = serializers.SerializerMethodField()

    class Meta(MenuItemSerializer.Meta):
        fields = MenuItemSerializer.Meta.fields + ['addon_groups']

    def get_addon_groups(self, obj):
        groups = AddonGroup.objects.filter(item_groups__item=obj)
        return AddonGroupSerializer(groups, many=True).data


class OfferSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(
        read_only=True, source='merchant.business_name')

    class Meta:
        model = Offer
        fields = [
            'id', 'merchant', 'merchant_name', 'title', 'description',
            'image', 'discount_type', 'discount_value', 'max_discount',
            'min_order_amount', 'valid_from', 'valid_to', 'is_active',
        ]
        read_only_fields = ['merchant']
