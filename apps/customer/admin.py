from django.contrib import admin
from .models import CustomerProfile, SavedAddress, PaymentMethod, Cart, CartItem


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone')
    search_fields = ('user__email',)


@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'label', 'address', 'is_default')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'method_type', 'is_default')


admin.site.register(Cart)
admin.site.register(CartItem)
