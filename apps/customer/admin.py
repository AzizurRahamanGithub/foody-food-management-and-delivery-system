from django.contrib import admin
from .models import (CustomerProfile, SavedAddress, PaymentMethod,
                     Referral, Wallet, WalletTransaction,
                     Cart, CartItem, FavoriteItem, RecentSearch)


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'gender', 'referral_code',
                    'referred_by', 'wallet_balance')
    list_filter = ('gender',)
    search_fields = ('user__email', 'referral_code',
                     'user__full_name')
    readonly_fields = ('referral_code',)


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'custom_label', 'address',
                    'is_default')
    list_filter = ('label', 'is_default')
    search_fields = ('user__email', 'address')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'card_last4', 'is_default')
    list_filter = ('method_type', 'is_default')


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('referrer', 'referred_user', 'status',
                    'reward_amount', 'rewarded_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('referrer__email', 'referred_user__email',
                     'referral_code_used')
    readonly_fields = ('rewarded_at',)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__email',)


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ('wallet', 'transaction_type', 'amount',
                    'description', 'reference', 'created_at')
    list_filter = ('transaction_type',)
    search_fields = ('wallet__user__email', 'description',
                     'reference')


admin.site.register(Cart)
admin.site.register(CartItem)


@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'item', 'created_at')
    search_fields = ('user__email', 'item__name')


@admin.register(RecentSearch)
class RecentSearchAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'search_type', 'created_at')
    list_filter = ('search_type',)
    search_fields = ('user__email', 'query')
