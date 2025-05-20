from django.contrib import admin
from .models import MerchantProfile, Category, MenuItem, AddonGroup, Addon, MenuItemAddon, Offer


@admin.register(MerchantProfile)
class MerchantProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'business_type',
                    'verification_status', 'is_open', 'city')
    list_filter = ('verification_status', 'business_type', 'is_open')
    search_fields = ('business_name', 'user__email')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'sort_order')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'merchant', 'category', 'price', 'is_available')
    list_filter = ('is_available', 'is_veg')
    search_fields = ('name', 'merchant__business_name')


admin.site.register(AddonGroup)
admin.site.register(Addon)
admin.site.register(MenuItemAddon)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('title', 'merchant', 'discount_type',
                    'discount_value', 'is_active')
    list_filter = ('discount_type', 'is_active')
