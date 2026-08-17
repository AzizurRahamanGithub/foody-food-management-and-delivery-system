import random
import math
from decimal import Decimal
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Q, Count, Avg, F
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from apps.core.response import success_response, failure_response
from apps.core.crud import DynamicModelViewSet
from apps.merchant.models import (MerchantProfile, GlobalCategory,
                                  MenuItem, Offer, Category, Addon,
                                  ItemReview)
from apps.orders.models import Order, OrderItem, DeliveryTask, Review
from apps.orders.serializers import (
    OrderSerializer, OrderCreateSerializer, ReviewSerializer)
from apps.auths.models import CustomUser
from .models import (CustomerProfile, SavedAddress, PaymentMethod,
                     Referral, Wallet, WalletTransaction,
                     Cart, CartItem, FavoriteItem, RecentSearch)
from .serializers import (CustomerProfileSerializer,
                          SavedAddressSerializer,
                          PaymentMethodSerializer, ReferralSerializer,
                          ReferralInviteSerializer, WalletSerializer,
                          WalletTransactionSerializer,
                          CartSerializer, CartItemSerializer,
                          RestaurantCardSerializer,
                          RestaurantDetailSerializer)

REFERRAL_MIN_ORDER = Decimal('4000.00')
REFERRAL_REWARD = Decimal('1000.00')


class CustomerRolePermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == 'customer'


class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        return success_response(
            "Profile fetched",
            CustomerProfileSerializer(profile).data)

    def put(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        serializer = CustomerProfileSerializer(
            profile, data=request.data, partial=True,
            context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return success_response(
                "Profile updated", serializer.data)
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


class ReferralMyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        referrals = Referral.objects.filter(
            referrer=request.user).select_related('referred_user')
        return success_response("My referrals", {
            "referral_code": profile.referral_code,
            "total_referrals": referrals.count(),
            "earned": referrals.filter(status='earned').count(),
            "pending": referrals.filter(status='pending').count(),
            "referrals": ReferralSerializer(referrals, many=True).data,
        })


class ReferralInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReferralInviteSerializer(data=request.data)
        if not serializer.is_valid():
            return failure_response("Invalid data", serializer.errors)
        email = serializer.validated_data['email']
        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        return success_response("Invitation ready", {
            "email": email,
            "referral_code": profile.referral_code,
            "message": (
                f"Your friend will receive a link to sign up with "
                f"code {profile.referral_code}. They get free delivery "
                f"on their first order!"),
        })


def apply_referral_code(user, referral_code):
    if not referral_code:
        return
    try:
        referrer_profile = CustomerProfile.objects.get(
            referral_code=referral_code)
    except CustomerProfile.DoesNotExist:
        return
    if referrer_profile.user == user:
        return
    if Referral.objects.filter(referred_user=user).exists():
        return
    Referral.objects.create(
        referrer=referrer_profile.user,
        referred_user=user,
        referral_code_used=referral_code,
        status='pending',
        reward_amount=REFERRAL_REWARD,
    )


def process_referral_reward(order):
    if order.total < REFERRAL_MIN_ORDER:
        return
    try:
        referred_profile = CustomerProfile.objects.get(
            user=order.customer)
    except CustomerProfile.DoesNotExist:
        return
    referral = Referral.objects.filter(
        referred_user=order.customer,
        status='pending'
    ).first()
    if not referral:
        return
    referral.status = 'earned'
    referral.first_order = order
    referral.rewarded_at = timezone.now()
    referral.save()
    wallet, _ = Wallet.objects.get_or_create(
        user=referral.referrer)
    wallet.balance += REFERRAL_REWARD
    wallet.save()
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type='credit',
        amount=REFERRAL_REWARD,
        description=(
            f"Referral reward for referring "
            f"{order.customer.email}"),
        reference=f"REF-{referral.id}-{order.id}",
    )


def has_referral_benefit(user):
    return Referral.objects.filter(
        referred_user=user, status='pending').exists()


class HomeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        offers = Offer.objects.filter(is_active=True)[:6]

        food_subcats = GlobalCategory.objects.filter(
            is_active=True,
            merchants__business_type='restaurant',
            merchants__verification_status='approved'
        ).distinct().order_by('name')[:20]

        store_subcats = GlobalCategory.objects.filter(
            is_active=True,
            merchants__business_type='store',
            merchants__verification_status='approved'
        ).distinct().order_by('name')[:20]

        store_filter_presets = [
            {
                "key": "grocery_near_you",
                "name": "Grocery Stores Near You",
                "description": "Fresh groceries from nearby stores",
                "store_filter": "grocery_near_you",
            },
            {
                "key": "drinks_essentials",
                "name": "Drinks & Essentials",
                "description": "Beverages, snacks & daily essentials",
                "store_filter": "drinks_essentials",
            },
            {
                "key": "local_stores",
                "name": "Local Stores",
                "description": "Support local businesses in your area",
                "store_filter": "local_stores",
            },
            {
                "key": "recommended",
                "name": "Recommended for You",
                "description": "Top-rated stores picked for you",
                "store_filter": "recommended",
            },
        ]

        data = {
            "special_offers": [{
                "id": o.id, "title": o.title, "image": o.image,
                "discount_type": o.discount_type,
                "discount_value": str(o.discount_value),
                "merchant_name": o.merchant.business_name,
            } for o in offers],
            "food_subcategories": [{
                "id": c.id, "name": c.name, "image": c.image,
            } for c in food_subcats],
            "store_subcategories": [{
                "id": c.id, "name": c.name, "image": c.image,
            } for c in store_subcats],
            "store_filter_presets": store_filter_presets,
        }
        return success_response("Home data", data)


def calc_distance(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]):
        return None
    R = 6371
    d_lat = math.radians(float(lat2) - float(lat1))
    d_lon = math.radians(float(lon2) - float(lon1))
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(float(lat1))) *
         math.cos(math.radians(float(lat2))) *
         math.sin(d_lon / 2) ** 2)
    return round(R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


class HomeListingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        item_type = request.query_params.get('type')
        subcategory = request.query_params.get('subcategory')
        store_filter = request.query_params.get('store_filter')
        sort = request.query_params.get('sort', 'popular')
        search = request.query_params.get('search')
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))

        items = MenuItem.objects.filter(
            is_available=True,
            merchant__verification_status='approved'
        ).select_related('merchant', 'category')

        if item_type == 'food':
            items = items.filter(
                merchant__business_type='restaurant')
        elif item_type == 'store':
            items = items.filter(
                merchant__business_type='store')

        if subcategory:
            items = items.filter(
                merchant__categories__id=subcategory)

        if store_filter and item_type == 'store':
            items = self.apply_store_filter(items, store_filter,
                                           request.user)

        if search:
            items = items.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(merchant__business_name__icontains=search))

        if sort == 'popular':
            items = items.annotate(
                order_count=Count('orderitem')
            ).order_by('-order_count', '-rating')
        elif sort == 'nearby':
            profile, _ = CustomerProfile.objects.get_or_create(
                user=request.user)
            if profile.default_latitude and profile.default_longitude:
                user_lat = float(profile.default_latitude)
                user_lon = float(profile.default_longitude)
                merchant_ids = list(
                    MerchantProfile.objects.filter(
                        verification_status='approved'
                    ).values_list('id', flat=True))
                scored = []
                for mid in merchant_ids:
                    m = MerchantProfile.objects.get(pk=mid)
                    d = calc_distance(
                        user_lat, user_lon,
                        m.latitude, m.longitude)
                    scored.append((mid, d if d else 9999))
                scored.sort(key=lambda x: x[1])
                nearby_ids = [s[0] for s in scored[:30]]
                items = items.filter(
                    merchant_id__in=nearby_ids)
            items = items.order_by('merchant__latitude')
        elif sort == 'fast_delivery':
            items = items.order_by(
                'merchant__delivery_time_min', '-rating')
        elif sort == 'recommended':
            items = items.filter(
                merchant__is_featured=True
            ).order_by('-rating')
        elif sort == 'price_low':
            items = items.order_by('price')
        elif sort == 'price_high':
            items = items.order_by('-price')
        elif sort == 'rating':
            items = items.order_by('-rating')

        total = items.count()
        start = (page - 1) * page_size
        end = start + page_size
        page_items = items[start:end]

        favorite_ids = set(
            FavoriteItem.objects.filter(
                user=request.user,
                item__in=page_items
            ).values_list('item_id', flat=True))

        merchant_ids = set(
            i.merchant_id for i in page_items)
        merchants = {
            m.id: m for m in
            MerchantProfile.objects.filter(id__in=merchant_ids)}

        user_lat = None
        user_lon = None
        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        if profile.default_latitude and profile.default_longitude:
            user_lat = float(profile.default_latitude)
            user_lon = float(profile.default_longitude)

        result = []
        for item in page_items:
            merchant = merchants.get(item.merchant_id)
            distance = None
            if merchant and user_lat and user_lon:
                distance = calc_distance(
                    user_lat, user_lon,
                    merchant.latitude, merchant.longitude)

            active_offer = None
            offers = Offer.objects.filter(
                merchant=item.merchant,
                is_active=True,
                items=item)
            if not offers.exists():
                offers = Offer.objects.filter(
                    merchant=item.merchant,
                    is_active=True,
                    items__isnull=True)
            offer = offers.first()
            if offer:
                active_offer = {
                    "id": offer.id,
                    "title": offer.title,
                    "discount_type": offer.discount_type,
                    "discount_value": str(offer.discount_value),
                }

            result.append({
                "id": item.id,
                "name": item.name,
                "image": item.image,
                "price": str(item.effective_price),
                "original_price": str(item.price),
                "rating": float(item.rating),
                "is_veg": item.is_veg,
                "preparation_time_min": item.preparation_time_min,
                "stock_quantity": item.stock_quantity,
                "is_favorited": item.id in favorite_ids,
                "offer": active_offer,
                "merchant": {
                    "id": merchant.id,
                    "name": merchant.business_name,
                    "delivery_time_min": merchant.delivery_time_min,
                    "address": merchant.address,
                } if merchant else None,
                "distance_km": distance,
            })

        return success_response("Items", {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size),
            "items": result,
        })

    def apply_store_filter(self, items, store_filter, user):
        if store_filter == 'grocery_near_you':
            items = items.filter(
                Q(merchant__categories__name__icontains='grocery') |
                Q(merchant__categories__name__icontains='fruit') |
                Q(merchant__categories__name__icontains='vegetable') |
                Q(merchant__categories__name__icontains='meat') |
                Q(merchant__categories__name__icontains='fish') |
                Q(merchant__categories__name__icontains='bakery')
            ).distinct()
            profile, _ = CustomerProfile.objects.get_or_create(
                user=user)
            if (profile.default_latitude
                    and profile.default_longitude):
                user_lat = float(profile.default_latitude)
                user_lon = float(profile.default_longitude)
                merchant_ids = list(
                    MerchantProfile.objects.filter(
                        business_type='store',
                        verification_status='approved'
                    ).values_list('id', flat=True))
                scored = []
                for mid in merchant_ids:
                    m = MerchantProfile.objects.get(pk=mid)
                    d = calc_distance(
                        user_lat, user_lon,
                        m.latitude, m.longitude)
                    if d is not None and d <= 10:
                        scored.append((mid, d))
                scored.sort(key=lambda x: x[1])
                nearby_ids = [s[0] for s in scored[:30]]
                items = items.filter(
                    merchant_id__in=nearby_ids)

        elif store_filter == 'drinks_essentials':
            items = items.filter(
                Q(merchant__categories__name__icontains='drink') |
                Q(merchant__categories__name__icontains='beverage') |
                Q(merchant__categories__name__icontains='water') |
                Q(merchant__categories__name__icontains='snack') |
                Q(merchant__categories__name__icontains='essential') |
                Q(merchant__categories__name__icontains='dairy') |
                Q(merchant__categories__name__icontains='milk')
            ).distinct()

        elif store_filter == 'local_stores':
            profile, _ = CustomerProfile.objects.get_or_create(
                user=user)
            if (profile.default_latitude
                    and profile.default_longitude):
                user_lat = float(profile.default_latitude)
                user_lon = float(profile.default_longitude)
                merchant_ids = list(
                    MerchantProfile.objects.filter(
                        business_type='store',
                        verification_status='approved'
                    ).values_list('id', flat=True))
                scored = []
                for mid in merchant_ids:
                    m = MerchantProfile.objects.get(pk=mid)
                    d = calc_distance(
                        user_lat, user_lon,
                        m.latitude, m.longitude)
                    if d is not None and d <= 15:
                        scored.append((mid, d))
                scored.sort(key=lambda x: x[1])
                nearby_ids = [s[0] for s in scored[:30]]
                items = items.filter(
                    merchant_id__in=nearby_ids)

        elif store_filter == 'recommended':
            items = items.filter(
                merchant__is_featured=True
            ).order_by('-rating')

        return items


class RestaurantListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q')
        business_type = request.query_params.get('type')
        category = request.query_params.get('category')
        queryset = MerchantProfile.objects.filter(
            verification_status='approved')

        if business_type:
            queryset = queryset.filter(business_type=business_type)
        if q:
            queryset = queryset.filter(
                Q(business_name__icontains=q) |
                Q(address__icontains=q))
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
            "Restaurant details",
            RestaurantDetailSerializer(restaurant).data)


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
            return failure_response(
                "Query parameter 'q' is required")
        restaurants = MerchantProfile.objects.filter(
            verification_status='approved',
            business_name__icontains=q)
        items = MenuItem.objects.filter(
            merchant__verification_status='approved',
            name__icontains=q)[:20]
        data = {
            "restaurants": RestaurantCardSerializer(
                restaurants, many=True).data,
            "items": [{
                "id": i.id, "name": i.name,
                "price": str(i.effective_price),
                "image": i.image,
                "merchant_name": i.merchant.business_name,
            } for i in items],
        }
        return success_response("Search results", data)


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return success_response(
            "Cart fetched", CartSerializer(cart).data)


class CartAddItemView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        addon_ids = request.data.get('addon_ids', []) or []

        item = get_object_or_404(MenuItem, pk=item_id)
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart, item=item, defaults={'quantity': 0})
        cart_item.quantity += quantity
        cart_item.save()

        addons = Addon.objects.filter(id__in=addon_ids)
        cart_item.addons.set(addons)

        return success_response(
            "Item added to cart", CartSerializer(cart).data,
            status.HTTP_201_CREATED if created
            else status.HTTP_200_OK)


class CartUpdateItemView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        cart_item = get_object_or_404(
            CartItem, pk=pk, cart__user=request.user)
        quantity = request.data.get('quantity')
        if quantity is not None:
            cart_item.quantity = int(quantity)
        addon_ids = request.data.get('addon_ids')
        if addon_ids is not None:
            cart_item.addons.set(
                Addon.objects.filter(id__in=addon_ids))
        cart_item.save()
        return success_response(
            "Cart updated",
            CartSerializer(cart_item.cart).data)


class CartRemoveItemView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        cart_item = get_object_or_404(
            CartItem, pk=pk, cart__user=request.user)
        cart = cart_item.cart
        cart_item.delete()
        return success_response(
            "Item removed from cart",
            CartSerializer(cart).data)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return success_response("Cart cleared")


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

        merchant = get_object_or_404(
            MerchantProfile, pk=data['merchant_id'])
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = list(cart.items.all())
        if not cart_items:
            return failure_response("Cart is empty")

        if any(ci.item.merchant_id != merchant.id
               for ci in cart_items):
            return failure_response(
                "Cart contains items from another restaurant")

        try:
            with transaction.atomic():
                subtotal = sum(
                    Decimal(str(ci.line_total))
                    for ci in cart_items)
                discount = Decimal('0.00')
                if data.get('offer_id'):
                    offer = Offer.objects.filter(
                        id=data['offer_id'], merchant=merchant,
                        is_active=True).first()
                    if offer and subtotal >= offer.min_order_amount:
                        if offer.discount_type == \
                                Offer.DiscountType.PERCENT:
                            discount = (
                                subtotal * offer.discount_value / 100)
                            if offer.max_discount:
                                discount = min(
                                    discount, offer.max_discount)
                        else:
                            discount = offer.discount_value
                        discount = min(discount, subtotal)

                delivery_fee = get_delivery_fee()
                if has_referral_benefit(request.user):
                    delivery_fee = Decimal('0.00')
                service_fee = Decimal('0.00')
                total = subtotal - discount + delivery_fee + service_fee

                order = Order.objects.create(
                    customer=request.user,
                    merchant=merchant,
                    offer=Offer.objects.filter(
                        id=data['offer_id']
                    ).first() if data.get('offer_id') else None,
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
                    addon_text = ", ".join(
                        ci.addons.values_list('name', flat=True))
                    OrderItem.objects.create(
                        order=order,
                        item=ci.item,
                        item_name=ci.item.name,
                        item_price=ci.item.effective_price,
                        quantity=ci.quantity,
                        addon_text=addon_text,
                        total=ci.line_total,
                    )

                order.add_status_log(
                    Order.Status.PENDING,
                    changed_by=request.user)
                order.accepted_at = None
                order.save()

                DeliveryTask.objects.create(
                    order=order,
                    status=DeliveryTask.Status.AVAILABLE,
                    pickup_code=str(random.randint(1000, 9999)),
                )

                cart.items.all().delete()

            from apps.orders.tracking import broadcast_order_update
            broadcast_order_update(
                order, event_type='new_order')

            from apps.notification.utils import (
                notify_order_placed)
            notify_order_placed(request.user, order)

            return success_response(
                "Order placed successfully",
                OrderSerializer(order).data,
                status.HTTP_201_CREATED)
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
            "Orders fetched",
            OrderSerializer(orders, many=True).data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_object_or_404(
            Order, pk=pk, customer=request.user)
        return success_response(
            "Order details", OrderSerializer(order).data)


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        order = get_object_or_404(
            Order, pk=pk, customer=request.user)
        if order.status not in [
                Order.Status.PENDING, Order.Status.ACCEPTED]:
            return failure_response(
                "Order can only be cancelled while "
                "pending or accepted")
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
        broadcast_order_update(
            order, event_type='order_cancelled')
        from apps.notification.utils import (
            notify_order_cancelled)
        notify_order_cancelled(
            request.user, order,
            reason=request.data.get('reason', ''))
        return success_response(
            "Order cancelled",
            OrderSerializer(order).data)


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
            Order, pk=request.data.get('order_id'),
            customer=request.user)
        if order.status != Order.Status.DELIVERED:
            return failure_response(
                "You can review only delivered orders")
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
            "Review submitted",
            OrderSerializer(review).data,
            status.HTTP_201_CREATED)


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wallet, _ = Wallet.objects.get_or_create(
            user=request.user)
        transactions = wallet.transactions.all()[:20]
        return success_response("Wallet", {
            "balance": str(wallet.balance),
            "transactions": WalletTransactionSerializer(
                transactions, many=True).data,
        })


class ReferralApplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get('referral_code', '').strip()
        if not code:
            return failure_response("Referral code is required")

        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        if profile.referred_by:
            return failure_response(
                "You already used a referral code")

        try:
            referrer_profile = CustomerProfile.objects.get(
                referral_code=code)
        except CustomerProfile.DoesNotExist:
            return failure_response("Invalid referral code")

        if referrer_profile.user == request.user:
            return failure_response(
                "You cannot refer yourself")

        existing = Referral.objects.filter(
            referred_user=request.user).first()
        if existing:
            return failure_response(
                "You already have a referral record")

        referral = Referral.objects.create(
            referrer=referrer_profile.user,
            referred_user=request.user,
            referral_code_used=code,
            status='pending',
            reward_amount=REFERRAL_REWARD,
        )
        profile.referred_by = referrer_profile.user
        profile.save()

        return success_response("Referral code applied", {
            "referral_code": code,
            "referrer": referrer_profile.user.email,
            "benefit": (
                "You get free delivery on your first order! "
                "Your referrer earns ₦1,000 after your first "
                "order of ₦4,000 or more."),
        })


class PaystackInitializeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order = get_object_or_404(
            Order, pk=request.data.get('order_id'),
            customer=request.user)
        if order.payment_method != Order.PaymentMethod.CARD:
            return failure_response("Order is not a card payment")

        from .payments import paystack_initialize
        reference = order.payment_reference or \
            f"TP-{order.id}-{order.order_number}"
        callback_url = request.data.get('callback_url') or \
            request.build_absolute_uri(
                '/api/v1/customer/payment/verify/')

        result = paystack_initialize(
            email=request.user.email,
            amount=order.total,
            reference=reference,
            callback_url=callback_url,
        )
        if not result['success']:
            return failure_response(
                "Could not initialize payment",
                result.get('error'),
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
            payment_reference=reference,
            customer=request.user).first()
        if not order:
            return failure_response(
                "No order found for this reference",
                status=status.HTTP_404_NOT_FOUND)

        from .payments import paystack_verify
        result = paystack_verify(reference)
        if not result['success']:
            order.payment_status = Order.PaymentStatus.FAILED
            order.save(update_fields=['payment_status'])
            return failure_response(
                "Payment verification failed",
                result.get('error'),
                status.HTTP_402_PAYMENT_REQUIRED)

        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=['payment_status'])

        if order.customer:
            process_referral_reward(order)

        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(
            order, event_type='payment_verified')
        return success_response(
            "Payment verified",
            {
                'order_id': order.id,
                'order_number': order.order_number,
                'payment_status': order.payment_status,
            })


class ItemReviewCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from apps.merchant.serializers import \
            ItemReviewCreateSerializer
        serializer = ItemReviewCreateSerializer(
            data=request.data,
            context={'request': request})
        if serializer.is_valid():
            review = serializer.save()
            from apps.merchant.serializers import \
                ItemReviewSerializer
            return success_response(
                "Item review submitted",
                ItemReviewSerializer(review).data,
                status.HTTP_201_CREATED)
        return failure_response("Invalid data", serializer.errors)


class ItemReviewsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        from apps.merchant.models import MenuItem, ItemReview
        from apps.merchant.serializers import ItemReviewSerializer
        item = get_object_or_404(MenuItem, pk=pk)
        reviews = ItemReview.objects.filter(item=item)
        return success_response(
            "Item reviews",
            ItemReviewSerializer(reviews, many=True).data)


class FavoriteToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item_id')
        if not item_id:
            return failure_response("item_id is required")
        item = get_object_or_404(MenuItem, pk=item_id)
        fav, created = FavoriteItem.objects.get_or_create(
            user=request.user, item=item)
        if not created:
            fav.delete()
            return success_response("Removed from favorites", {
                "item_id": item_id, "is_favorited": False})
        return success_response("Added to favorites", {
            "item_id": item_id, "is_favorited": True},
            status.HTTP_201_CREATED)


class HomeItemDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        item = get_object_or_404(
            MenuItem.objects.select_related('merchant', 'category'),
            pk=pk)
        merchant = item.merchant

        profile, _ = CustomerProfile.objects.get_or_create(
            user=request.user)
        distance = None
        if (profile.default_latitude and profile.default_longitude
                and merchant.latitude and merchant.longitude):
            distance = calc_distance(
                float(profile.default_latitude),
                float(profile.default_longitude),
                float(merchant.latitude),
                float(merchant.longitude))

        is_favorited = FavoriteItem.objects.filter(
            user=request.user, item=item).exists()

        active_offer = None
        offers = Offer.objects.filter(
            merchant=merchant, is_active=True, items=item)
        if not offers.exists():
            offers = Offer.objects.filter(
                merchant=merchant, is_active=True,
                items__isnull=True)
        offer = offers.first()
        if offer:
            active_offer = {
                "id": offer.id,
                "title": offer.title,
                "description": offer.description,
                "discount_type": offer.discount_type,
                "discount_value": str(offer.discount_value),
                "max_discount": str(offer.max_discount)
                    if offer.max_discount else None,
            }

        from apps.merchant.serializers import AddonGroupSerializer
        addon_groups = AddonGroupSerializer(
            AddonGroup.objects.filter(item_groups__item=item),
            many=True).data

        reviews = ItemReview.objects.filter(
            item=item).select_related('customer'
            ).order_by('-created_at')[:10]
        review_data = [{
            "id": r.id,
            "customer_name": r.customer.full_name
                or r.customer.email,
            "rating": r.rating,
            "comment": r.comment,
            "created_at": r.created_at.isoformat(),
        } for r in reviews]
        avg_rating = ItemReview.objects.filter(
            item=item).aggregate(
            avg=Avg('rating'))['avg'] or 0
        total_reviews = ItemReview.objects.filter(
            item=item).count()

        return success_response("Item detail", {
            "id": item.id,
            "name": item.name,
            "description": item.description,
            "image": item.image,
            "price": str(item.price),
            "discount_price": str(item.discount_price)
                if item.discount_price else None,
            "effective_price": str(item.effective_price),
            "is_available": item.is_available,
            "is_veg": item.is_veg,
            "preparation_time_min": item.preparation_time_min,
            "stock_quantity": item.stock_quantity,
            "rating": float(item.rating),
            "is_favorited": is_favorited,
            "offer": active_offer,
            "addon_groups": addon_groups,
            "merchant": {
                "id": merchant.id,
                "name": merchant.business_name,
                "address": merchant.address,
                "delivery_time_min": merchant.delivery_time_min,
                "logo": merchant.logo,
            },
            "distance_km": distance,
            "reviews": {
                "average_rating": round(float(avg_rating), 2),
                "total": total_reviews,
                "recent": review_data,
            },
        })


class RecentSearchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        searches = RecentSearch.objects.filter(
            user=request.user)[:20]
        return success_response("Recent searches", [{
            "id": s.id,
            "query": s.query,
            "search_type": s.search_type,
            "created_at": s.created_at.isoformat(),
        } for s in searches])


class RecentSearchSaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        search_type = request.data.get('search_type', 'general')
        if not query:
            return failure_response("query is required")
        search = RecentSearch.objects.create(
            user=request.user,
            query=query,
            search_type=search_type,
            latitude=request.data.get('latitude'),
            longitude=request.data.get('longitude'),
        )
        return success_response("Search saved", {
            "id": search.id,
            "query": search.query,
            "search_type": search.search_type},
            status.HTTP_201_CREATED)


class RecentSearchDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        search = RecentSearch.objects.filter(
            user=request.user, pk=pk).first()
        if not search:
            return failure_response("Not found",
                                    status.HTTP_404_NOT_FOUND)
        search.delete()
        return success_response("Deleted")

    def delete_all(self, request):
        count = RecentSearch.objects.filter(
            user=request.user).delete()[0]
        return success_response("All cleared",
                                {"deleted": count})
