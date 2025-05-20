from django.contrib import admin
from .models import Order, OrderItem, OrderStatusLog, DeliveryTask, Review


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'merchant', 'status',
                    'payment_method', 'total', 'placed_at')
    list_filter = ('status', 'payment_method', 'payment_status')
    search_fields = ('order_number', 'customer__email',
                     'merchant__business_name')
    inlines = [OrderItemInline]


@admin.register(OrderStatusLog)
class OrderStatusLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(DeliveryTask)
class DeliveryTaskAdmin(admin.ModelAdmin):
    list_display = ('order', 'rider', 'status', 'pickup_code',
                    'picked_up_at', 'delivered_at')
    list_filter = ('status',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('order', 'rating', 'rider_rating', 'created_at')
