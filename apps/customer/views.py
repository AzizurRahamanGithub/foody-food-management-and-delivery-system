import random
from decimal import Decimal
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q
from django.db import transaction
from django.shortcuts import get_object_or_404
from apps.core.response import success_response, failure_response
from apps.core.crud import DynamicModelViewSet
from apps.merchant.models import MerchantProfile, MenuItem, Offer, Category, Addon
from apps.orders.models import Order, OrderItem, DeliveryTask, Review
from apps.orders.serializers import (
    OrderSerializer, OrderCreateSerializer, ReviewSerializer)
from apps.auths.models import CustomUser
from .models import CustomerProfile, SavedAddress, PaymentMethod, Cart, CartItem
from .serializers import (CustomerProfileSerializer, SavedAddressSerializer,
                          PaymentMethodSerializer, CartSerializer,
                          CartItemSerializer, RestaurantCardSerializer,
                          RestaurantDetailSerializer)


class CustomerRolePermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == 'customer'


class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        return success_response(
            "Profile fetched", CustomerProfileSerializer(profile).data)

    def put(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
        serializer = CustomerProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            user = request.user
            if 'full_name' in request.data:
                user.full_name = request.data['full_name']
                user.save()
            return success_response("Profile updated", serializer.data)
        return failure_response("Invalid data", serializer.errors)


class SavedAddressViewSet(DynamicModelViewSet):
    serializer_class = SavedAddressSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = SavedAddress
        kwargs['serializer_class'] = SavedAddressSerializer
        kwargs['item_name'] = 'Address'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return SavedAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save()


class PaymentMethodViewSet(DynamicModelViewSet):
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = PaymentMethod
        kwargs['serializer_class'] = PaymentMethodSerializer
        kwargs['item_name'] = 'PaymentMethod'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        return serializer.save()


class HomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        restaurants = MerchantProfile.objects.filter(
            business_type='restaurant', verification_status='approved')
        stores = MerchantProfile.objects.filter(
            business_type='store', verification_status='approved')

        offers = Offer.objects.filter(is_active=True)[:6]

        # Category tiles derived from restaurant categories
        seen = set()
        food_categories = []
        for c in Category.objects.filter(
                merchant__business_type='restaurant',
                merchant__verification_status='approved').order_by('id')[:40]:
            if c.name.lower() in seen:
                continue
            seen.add(c.name.lower())
            food_categories.append({
                "id": c.id, "name": c.name, "image": c.image,
            })
            if len(food_categories) >= 8:
                break

        data = {
            "special_offers": [{
                "id": o.id, "title": o.title, "image": o.image,
                "discount_type": o.discount_type,
                "discount_value": str(o.discount_value),
                "merchant_name": o.merchant.business_name,
            } for o in offers],
            "food_categories": food_categories,
            "popular_restaurants": RestaurantCardSerializer(
                restaurants.filter(is_featured=True)[:8], many=True).data,
            "nearby_restaurants": RestaurantCardSerializer(
                restaurants[:8], many=True).data,
            "fast_delivery": RestaurantCardSerializer(
                restaurants.filter(delivery_time_min__lte=25)[:8], many=True).data,
            "stores": RestaurantCardSerializer(stores[:8], many=True).data,
        }
        return success_response("Home data", data)


class RestaurantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q')
        business_type = request.query_params.get('type')
        category = request.query_params.get('category')
        queryset = MerchantProfile.objects.filter(verification_status='approved')

        if business_type:
            queryset = queryset.filter(business_type=business_type)
        if q:
            queryset = queryset.filter(
                Q(business_name__icontains=q) | Q(address__icontains=q))
        if category:
            queryset = queryset.filter(
                categories__id=category).distinct()

        return success_response(
            "Restaurants fetched",
            RestaurantCardSerializer(queryset, many=True).data)


class RestaurantDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        restaurant = get_object_or_404(MerchantProfile, pk=pk)
        return success_response(
            "Restaurant details", RestaurantDetailSerializer(restaurant).data)


class MenuItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from apps.merchant.serializers import MenuItemDetailSerializer
        item = get_object_or_404(MenuItem, pk=pk)
        return success_response(
            "Item details", MenuItemDetailSerializer(item).data)


class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q:
            return failure_response("Query parameter 'q' is required")
        restaurants = MerchantProfile.objects.filter(
            verification_status='approved',
            business_name__icontains=q)
        items = MenuItem.objects.filter(
            merchant__verification_status='approved',
            name__icontains=q)[:20]
        data = {
            "restaurants": RestaurantCardSerializer(restaurants, many=True).data,
            "items": [{
                "id": i.id, "name": i.name, "price": str(i.effective_price),
                "image": i.image, "merchant_name": i.merchant.business_name,
            } for i in items],
        }
        return success_response("Search results", data)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return success_response("Cart fetched", CartSerializer(cart).data)


class CartAddItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        addon_ids = request.data.get('addon_ids', []) or []

        item = get_object_or_404(MenuItem, pk=item_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, item=item,
            defaults={'quantity': 0})
        cart_item.quantity += quantity
        cart_item.save()

        addons = Addon.objects.filter(id__in=addon_ids)
        cart_item.addons.set(addons)

        return success_response(
            "Item added to cart", CartSerializer(cart).data,
            status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class CartUpdateItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        quantity = request.data.get('quantity')
        if quantity is not None:
            cart_item.quantity = int(quantity)
        addon_ids = request.data.get('addon_ids')
        if addon_ids is not None:
            cart_item.addons.set(Addon.objects.filter(id__in=addon_ids))
        cart_item.save()
        return success_response(
            "Cart updated", CartSerializer(cart_item.cart).data)


class CartRemoveItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        cart = cart_item.cart
        cart_item.delete()
        return success_response(
            "Item removed from cart", CartSerializer(cart).data)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return success_response("Cart cleared", CartSerializer(cart).data)


def get_delivery_fee(distance_km=None):
    from apps.admin_panel.models import PricingRule
    rule = PricingRule.objects.filter(is_active=True).first()
    if rule:
        return rule.base_fare
    return Decimal('30.00')


class CheckoutView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderCreateSerializer

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return failure_response("Invalid data", serializer.errors)
        data = serializer.validated_data

        merchant = get_object_or_404(MerchantProfile, pk=data['merchant_id'])
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = list(cart.items.all())
        if not cart_items:
            return failure_response("Cart is empty")

        # Make sure cart items belong to this merchant
        if any(ci.item.merchant_id != merchant.id for ci in cart_items):
            return failure_response(
                "Cart contains items from another restaurant")

        try:
            with transaction.atomic():
                subtotal = sum(Decimal(str(ci.line_total)) for ci in cart_items)
                discount = Decimal('0.00')
                if data.get('offer_id'):
                    offer = Offer.objects.filter(
                        id=data['offer_id'], merchant=merchant,
                        is_active=True).first()
                    if offer and subtotal >= offer.min_order_amount:
                        if offer.discount_type == Offer.DiscountType.PERCENT:
                            discount = subtotal * offer.discount_value / 100
                            if offer.max_discount:
                                discount = min(discount, offer.max_discount)
                        else:
                            discount = offer.discount_value
                        discount = min(discount, subtotal)

                delivery_fee = get_delivery_fee()
                service_fee = Decimal('0.00')
                total = subtotal - discount + delivery_fee + service_fee

                order = Order.objects.create(
                    customer=request.user,
                    merchant=merchant,
                    offer=Offer.objects.filter(
                        id=data['offer_id']).first() if data.get('offer_id') else None,
                    status=Order.Status.PENDING,
                    payment_method=data['payment_method'],
                    subtotal=subtotal,
                    delivery_fee=delivery_fee,
                    discount=discount,
                    service_fee=service_fee,
                    total=total,
                    delivery_address=data['delivery_address'],
                    delivery_latitude=data.get('delivery_latitude'),
                    delivery_longitude=data.get('delivery_longitude'),
                    note=data.get('note'),
                    is_scheduled=data['is_scheduled'],
                    schedule_at=data.get('schedule_at'),
                )

                for ci in cart_items:
                    addon_text = ", ".join(ci.addons.values_list('name', flat=True))
                    OrderItem.objects.create(
                        order=order,
                        item=ci.item,
                        item_name=ci.item.name,
                        item_price=ci.item.effective_price,
                        quantity=ci.quantity,
                        addon_text=addon_text,
                        total=ci.line_total,
                    )

                order.add_status_log(Order.Status.PENDING, changed_by=request.user)
                order.accepted_at = None
                order.save()

                DeliveryTask.objects.create(
                    order=order,
                    status=DeliveryTask.Status.AVAILABLE,
                    pickup_code=str(random.randint(1000, 9999)),
                )

                cart.items.all().delete()

            from apps.orders.tracking import broadcast_order_update
            broadcast_order_update(order, event_type='new_order')

            return success_response(
                "Order placed successfully",
                OrderSerializer(order).data, status.HTTP_201_CREATED)
        except Exception as e:
            return failure_response(
                "Order placement failed", str(e),
                status.HTTP_500_INTERNAL_SERVER_ERROR)


class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        status_filter = request.query_params.get('status')
        orders = Order.objects.filter(customer=request.user)
        if status_filter:
            orders = orders.filter(status=status_filter)
        return success_response(
            "Orders fetched", OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        return success_response("Order details", OrderSerializer(order).data)


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(Order, pk=pk, customer=request.user)
        if order.status not in [Order.Status.PENDING, Order.Status.ACCEPTED]:
            return failure_response(
                "Order can only be cancelled while pending or accepted")
        from django.utils import timezone as tz
        order.status = Order.Status.CANCELLED
        order.cancelled_at = tz.now()
        order.cancel_reason = request.data.get('reason', '')
        order.save()
        order.add_status_log(
            Order.Status.CANCELLED, changed_by=request.user,
            note=request.data.get('reason', ''))
        task = getattr(order, 'delivery_task', None)
        if task and task.status == DeliveryTask.Status.AVAILABLE:
            task.status = DeliveryTask.Status.CANCELLED
            task.save()
        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type='order_cancelled')
        return success_response("Order cancelled", OrderSerializer(order).data)


class TrackOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(Order, pk=pk)
        rider_location = None
        if order.rider:
            rider_location = {
                "latitude": str(order.rider.current_latitude),
                "longitude": str(order.rider.current_longitude),
            }
        data = OrderSerializer(order).data
        data['rider_location'] = rider_location
        return success_response("Live tracking", data)


class ReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order = get_object_or_404(
            Order, pk=request.data.get('order_id'), customer=request.user)
        if order.status != Order.Status.DELIVERED:
            return failure_response("You can review only delivered orders")
        if hasattr(order, 'review'):
            return failure_response("Order already reviewed")

        review = Review.objects.create(
            order=order,
            customer=request.user,
            merchant=order.merchant,
            rider=order.rider,
            rating=request.data.get('rating', 5),
            rider_rating=request.data.get('rider_rating'),
            comment=request.data.get('comment'),
        )
        return success_response(
            "Review submitted", ReviewSerializer(review).data,
            status.HTTP_201_CREATED)


class PaystackInitializeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order = get_object_or_404(
            Order, pk=request.data.get('order_id'), customer=request.user)
        if order.payment_method != Order.PaymentMethod.CARD:
            return failure_response("Order is not a card payment")

        from .payments import paystack_initialize
        reference = order.payment_reference or f"TP-{order.id}-{order.order_number}"
        callback_url = request.data.get('callback_url') or \
            request.build_absolute_uri('/api/v1/customer/payment/verify/')

        result = paystack_initialize(
            email=request.user.email,
            amount=order.total,
            reference=reference,
            callback_url=callback_url,
        )
        if not result['success']:
            return failure_response(
                "Could not initialize payment", result.get('error'),
                status.HTTP_502_BAD_GATEWAY)

        order.payment_reference = result['reference']
        order.save(update_fields=['payment_reference'])
        return success_response(
            "Payment initialized",
            {
                'authorization_url': result['authorization_url'],
                'reference': result['reference'],
                'order_id': order.id,
                'order_number': order.order_number,
                'amount': str(order.total),
            })


class PaystackVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reference = request.data.get('reference') or \
            request.query_params.get('reference')
        if not reference:
            return failure_response("Reference is required")

        order = Order.objects.filter(
            payment_reference=reference, customer=request.user).first()
        if not order:
            return failure_response(
                "No order found for this reference", status=status.HTTP_404_NOT_FOUND)

        from .payments import paystack_verify
        result = paystack_verify(reference)
        if not result['success']:
            order.payment_status = Order.PaymentStatus.FAILED
            order.save(update_fields=['payment_status'])
            return failure_response(
                "Payment verification failed", result.get('error'),
                status.HTTP_402_PAYMENT_REQUIRED)

        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=['payment_status'])
        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type='payment_verified')
        return success_response(
            "Payment verified",
            {
                'order_id': order.id,
                'order_number': order.order_number,
                'payment_status': order.payment_status,
            })
