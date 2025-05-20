from django.contrib import admin
from .models import RiderProfile, RiderDocument, BankInfo, Earning


@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'vehicle_type', 'is_online',
                    'verification_status')
    list_filter = ('is_online', 'verification_status', 'vehicle_type')
    search_fields = ('user__email',)


@admin.register(RiderDocument)
class RiderDocumentAdmin(admin.ModelAdmin):
    list_display = ('rider', 'doc_type', 'status', 'created_at')
    list_filter = ('status', 'doc_type')


@admin.register(BankInfo)
class BankInfoAdmin(admin.ModelAdmin):
    list_display = ('user', 'bank_name', 'account_holder', 'is_verified')


@admin.register(Earning)
class EarningAdmin(admin.ModelAdmin):
    list_display = ('rider', 'earning_type', 'amount', 'order', 'created_at')
    list_filter = ('earning_type',)
