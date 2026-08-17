from django.contrib import admin
from .models import (MerchantProfile, GlobalCategory, MerchantSchedule,
                     MerchantVerification, Category, MenuItem,
                     AddonGroup, Addon, MenuItemAddon, Offer, ItemReview)


@admin.register(GlobalCategory)
class GlobalCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'business_type',
                    'verification_status', 'is_open', 'city',
                    'manager_name', 'language')
    list_filter = ('verification_status', 'business_type', 'is_open',
                   'language')
    search_fields = ('business_name', 'user__email',
                     'manager_name', 'manager_email')


@admin.register(MerchantSchedule)
class MerchantScheduleAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'day_of_week', 'is_open',
                    'opening_time', 'closing_time')
    list_filter = ('is_open', 'day_of_week')
    search_fields = ('merchant__business_name',)


@admin.register(MerchantVerification)
class MerchantVerificationAdmin(admin.ModelAdmin):
    list_display = ('merchant', 'business_name', 'cac_registration_no',
                    'bank_name', 'status', 'reviewed_at')
    list_filter = ('status',)
    search_fields = ('merchant__business_name', 'business_name',
                     'cac_registration_no', 'bank_name')
    readonly_fields = ('reviewed_by', 'reviewed_at')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'sort_order')
    search_fields = ('name', 'merchant__business_name')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'category', 'price',
                    'is_available', 'stock_quantity')
    list_filter = ('is_available', 'is_veg')
    search_fields = ('name', 'merchant__business_name')


admin.site.register(MenuItemAddon)


@admin.register(AddonGroup)
class AddonGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'is_required',
                    'is_multiple_choice', 'max_selectable')
    list_filter = ('is_required', 'is_multiple_choice')
    search_fields = ('name', 'merchant__business_name')


@admin.register(Addon)
class AddonAdmin(admin.ModelAdmin):
    list_display = ('name', 'group', 'price', 'size',
                    'is_available')
    list_filter = ('size', 'is_available')
    search_fields = ('name', 'group__name')


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'merchant', 'discount_type',
                    'discount_value', 'is_active')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('title', 'merchant__business_name')


@admin.register(ItemReview)
class ItemReviewAdmin(admin.ModelAdmin):
    list_display = ('item', 'customer', 'rating', 'order', 'created_at')
    list_filter = ('rating',)
    search_fields = ('item__name', 'customer__email',
                     'item__merchant__business_name')
    readonly_fields = ('created_at',)
