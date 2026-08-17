from rest_framework import serializers
from apps.auths.models import CustomUser
from .models import (MerchantProfile, GlobalCategory, MerchantSchedule,
                     MerchantVerification, Category, MenuItem,
                     AddonGroup, Addon, MenuItemAddon, Offer, ItemReview)


class GlobalCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = GlobalCategory
        fields = ['id', 'name', 'image', 'is_active', 'created_at']
        read_only_fields = ['created_at']


class MerchantScheduleSerializer(serializers.ModelSerializer):
    day_display = serializers.CharField(
        source='get_day_of_week_display', read_only=True)

    class Meta:
        model = MerchantSchedule
        fields = ['id', 'day_of_week', 'day_display', 'is_open',
                  'opening_time', 'closing_time']
        read_only_fields = ['id']


class MerchantVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantVerification
        fields = ['id', 'business_name', 'cac_registration_no',
                  'cac_document', 'account_no', 'bank_name',
                  'status', 'rejection_reason', 'reviewed_at',
                  'created_at', 'updated_at']
        read_only_fields = ['status', 'rejection_reason', 'reviewed_at',
                            'created_at', 'updated_at']


class MerchantVerificationAdminSerializer(serializers.ModelSerializer):
    merchant_name = serializers.CharField(
        source='merchant.business_name', read_only=True)
    merchant_email = serializers.EmailField(
        source='merchant.user.email', read_only=True)

    class Meta:
        model = MerchantVerification
        fields = ['id', 'merchant', 'merchant_name', 'merchant_email',
                  'business_name', 'cac_registration_no', 'cac_document',
                  'account_no', 'bank_name', 'status', 'rejection_reason',
                  'reviewed_by', 'reviewed_at', 'created_at', 'updated_at']
        read_only_fields = ['status', 'rejection_reason', 'reviewed_by',
                            'reviewed_at', 'created_at', 'updated_at']


class MerchantProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True, source='user.id')
    email = serializers.EmailField(read_only=True, source='user.email')
    business_type = serializers.ChoiceField(
        choices=MerchantProfile.BusinessType.choices, required=False)
    verification_status = serializers.CharField(read_only=True)
    is_profile_setup = serializers.BooleanField(read_only=True)
    schedule = MerchantScheduleSerializer(many=True, read_only=True)
    categories_detail = GlobalCategorySerializer(
        source='categories', many=True, read_only=True)
    categories = serializers.PrimaryKeyRelatedField(
        queryset=GlobalCategory.objects.filter(is_active=True),
        many=True, required=False)
    verification = MerchantVerificationSerializer(read_only=True)
    language = serializers.ChoiceField(
        choices=MerchantProfile._meta.get_field('language').choices,
        required=False)

    class Meta:
        model = MerchantProfile
        fields = [
            'id', 'user_id', 'email', 'business_type', 'business_name',
            'description', 'logo', 'cover_photo',
            'manager_name', 'manager_email', 'manager_phone',
            'address', 'city', 'latitude', 'longitude',
            'shop_no', 'floor_name', 'building_name',
            'nearby_landmark', 'additional_direction',
            'is_open', 'delivery_time_min', 'min_order_amount',
            'general_notification_on', 'payment_notification_on',
            'app_update_notification_on', 'language',
            'categories', 'categories_detail',
            'verification_status', 'is_profile_setup',
            'is_featured', 'schedule', 'verification',
            'created_at',
        ]
        read_only_fields = [
            'verification_status', 'is_featured', 'created_at',
        ]

    def create(self, validated_data):
        categories_data = validated_data.pop('categories', [])
        profile = MerchantProfile.objects.create(**validated_data)
        if categories_data:
            profile.categories.set(categories_data)
        return profile

    def update(self, instance, validated_data):
        categories_data = validated_data.pop('categories', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if categories_data is not None:
            instance.categories.set(categories_data)
        return instance


class AddonSerializer(serializers.ModelSerializer):
    size_display = serializers.CharField(
        source='get_size_display', read_only=True)

    class Meta:
        model = Addon
        fields = ['id', 'name', 'price', 'size',
                  'size_display', 'is_available']
        read_only_fields = ['id']


class AddonGroupSerializer(serializers.ModelSerializer):
    addons = AddonSerializer(many=True, read_only=True)
    addon_count = serializers.SerializerMethodField()

    class Meta:
        model = AddonGroup
        fields = ['id', 'merchant', 'name', 'is_required',
                  'is_multiple_choice', 'max_selectable',
                  'addons', 'addon_count']
        read_only_fields = ['merchant']

    def get_addon_count(self, obj):
        return obj.addons.count()


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
            'stock_quantity', 'rating',
        ]
        read_only_fields = ['merchant']


class MenuItemListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        read_only=True, source='category.name')
    effective_price = serializers.DecimalField(
        read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'category', 'category_name', 'price',
                  'discount_price', 'effective_price', 'image',
                  'is_available', 'is_veg', 'preparation_time_min',
                  'stock_quantity', 'rating']


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
    item_names = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'merchant', 'merchant_name', 'title', 'description',
            'image', 'discount_type', 'discount_value', 'max_discount',
            'min_order_amount', 'items', 'item_names',
            'valid_from', 'valid_to', 'is_active',
        ]
        read_only_fields = ['merchant']

    def get_item_names(self, obj):
        return list(obj.items.values_list('name', flat=True))

    def validate_items(self, value):
        if value:
            merchant = self.context['request'].user.merchant_profile
            invalid = value.exclude(merchant=merchant)
            if invalid.exists():
                raise serializers.ValidationError(
                    "You can only select your own menu items.")
        return value


class ItemReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source='customer.full_name', read_only=True)
    item_name = serializers.CharField(
        source='item.name', read_only=True)

    class Meta:
        model = ItemReview
        fields = ['id', 'item', 'item_name', 'customer', 'customer_name',
                  'order', 'rating', 'comment', 'created_at']
        read_only_fields = ['customer', 'created_at']


class ItemReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemReview
        fields = ['id', 'item', 'order', 'rating', 'comment']
        read_only_fields = ['id']

    def validate_item(self, value):
        if not value.is_available:
            raise serializers.ValidationError(
                "This item is not available for review.")
        return value

    def validate(self, attrs):
        customer = self.context['request'].user
        item = attrs.get('item')
        order = attrs.get('order')

        if order:
            if order.customer != customer:
                raise serializers.ValidationError(
                    "You can only review items from your own orders.")
            if order.status != 'delivered':
                raise serializers.ValidationError(
                    "You can only review items from delivered orders.")
            if ItemReview.objects.filter(
                    item=item, customer=customer, order=order).exists():
                raise serializers.ValidationError(
                    "You already reviewed this item for this order.")
        else:
            if ItemReview.objects.filter(
                    item=item, customer=customer, order__isnull=True).exists():
                raise serializers.ValidationError(
                    "You already reviewed this item.")
        return attrs

    def create(self, validated_data):
        validated_data['customer'] = self.context['request'].user
        return super().create(validated_data)
