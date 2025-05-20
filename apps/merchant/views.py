from datetime import time
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
from apps.core.response import success_response, failure_response
from apps.core.crud import DynamicModelViewSet
from .models import (MerchantProfile, Category, MenuItem,
                     AddonGroup, Addon, Offer)
from .serializers import (MerchantProfileSerializer, CategorySerializer,
                          MenuItemSerializer, MenuItemDetailSerializer,
                          AddonGroupSerializer, AddonSerializer,
                          OfferSerializer)
from apps.auths.models import CustomUser


class MerchantRolePermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == 'merchant'


class MerchantProfileView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request):
        try:
            profile = MerchantProfile.objects.get(user=request.user)
            return success_response(
                "Profile fetched successfully", MerchantProfileSerializer(profile).data)
        except MerchantProfile.DoesNotExist:
            return failure_response("Merchant profile not found", status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            profile = MerchantProfile.objects.get(user=request.user)
        except MerchantProfile.DoesNotExist:
            return failure_response("Merchant profile not found", status=status.HTTP_404_NOT_FOUND)

        serializer = MerchantProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                "Profile updated successfully", serializer.data)
        return failure_response("Invalid data", serializer.errors)

    def post(self, request):
        """Complete onboarding step - convenience for full setup."""
        try:
            profile, created = MerchantProfile.objects.get_or_create(
                user=request.user)
        except Exception as e:
            return failure_response("Profile setup failed", str(e))
        serializer = MerchantProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                "Profile setup completed", serializer.data,
                status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return failure_response("Invalid data", serializer.errors)


class CategoryViewSet(DynamicModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [MerchantRolePermission]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = Category
        kwargs['serializer_class'] = CategorySerializer
        kwargs['item_name'] = 'Category'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return Category.objects.filter(merchant__user=self.request.user)

    def perform_create(self, serializer):
        merchant = MerchantProfile.objects.get(user=self.request.user)
        return serializer.save(merchant=merchant)


class MenuItemViewSet(DynamicModelViewSet):
    serializer_class = MenuItemSerializer
    permission_classes = [MerchantRolePermission]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = MenuItem
        kwargs['serializer_class'] = MenuItemSerializer
        kwargs['item_name'] = 'MenuItem'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return MenuItem.objects.filter(merchant__user=self.request.user)

    def perform_create(self, serializer):
        merchant = MerchantProfile.objects.get(user=self.request.user)
        return serializer.save(merchant=merchant)


class AddonGroupViewSet(DynamicModelViewSet):
    serializer_class = AddonGroupSerializer
    permission_classes = [MerchantRolePermission]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = AddonGroup
        kwargs['serializer_class'] = AddonGroupSerializer
        kwargs['item_name'] = 'AddonGroup'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return AddonGroup.objects.filter(merchant__user=self.request.user)

    def perform_create(self, serializer):
        merchant = MerchantProfile.objects.get(user=self.request.user)
        return serializer.save(merchant=merchant)


class AddonViewSet(DynamicModelViewSet):
    serializer_class = AddonSerializer
    permission_classes = [MerchantRolePermission]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = Addon
        kwargs['serializer_class'] = AddonSerializer
        kwargs['item_name'] = 'Addon'
        super().__init__(*args, **kwargs)


class OfferViewSet(DynamicModelViewSet):
    serializer_class = OfferSerializer
    permission_classes = [MerchantRolePermission]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = Offer
        kwargs['serializer_class'] = OfferSerializer
        kwargs['item_name'] = 'Offer'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return Offer.objects.filter(merchant__user=self.request.user)

    def perform_create(self, serializer):
        merchant = MerchantProfile.objects.get(user=self.request.user)
        return serializer.save(merchant=merchant)


class MerchantDashboardView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request):
        merchant = MerchantProfile.objects.get(user=request.user)
        today = timezone.now().date()
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, time.min))
        orders = merchant.orders
        today_orders = orders.filter(placed_at__gte=today_start)
        data = {
            "today_orders": today_orders.count(),
            "today_revenue": float(today_orders.exclude(
                status__in=['cancelled', 'rejected']).aggregate(
                total=Sum('total'))['total'] or 0),
            "total_orders": orders.count(),
            "active_items": merchant.menu_items.filter(is_available=True).count(),
            "pending_orders": orders.filter(status='pending').count(),
            "avg_rating": float(merchant.reviews.aggregate(
                avg=Avg('rating'))['avg'] or 0),
        }
        return success_response("Dashboard data", data)


class MerchantOrdersView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request):
        merchant = MerchantProfile.objects.get(user=request.user)
        status_filter = request.query_params.get('status')
        orders = merchant.orders.all()
        if status_filter:
            orders = orders.filter(status=status_filter)
        from apps.orders.serializers import OrderSerializer
        return success_response(
            "Orders fetched", OrderSerializer(orders, many=True).data)


class MerchantOrderDetailView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request, pk):
        merchant = MerchantProfile.objects.get(user=request.user)
        from apps.orders.models import Order
        from apps.orders.serializers import OrderSerializer
        order = merchant.orders.filter(pk=pk).first()
        if not order:
            return failure_response("Order not found", status=status.HTTP_404_NOT_FOUND)
        return success_response("Order details", OrderSerializer(order).data)


class MerchantOrderStatusView(APIView):
    permission_classes = [MerchantRolePermission]

    def post(self, request, pk):
        from apps.orders.models import Order
        from apps.orders.serializers import OrderSerializer
        merchant = MerchantProfile.objects.get(user=request.user)
        order = merchant.orders.filter(pk=pk).first()
        if not order:
            return failure_response("Order not found", status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action')
        allowed = {
            'accept': Order.Status.ACCEPTED,
            'reject': Order.Status.REJECTED,
            'preparing': Order.Status.PREPARING,
            'ready': Order.Status.READY,
        }
        if action not in allowed:
            return failure_response("Invalid action")

        new_status = allowed[action]
        if order.status in [Order.Status.CANCELLED, Order.Status.REJECTED,
                            Order.Status.DELIVERED]:
            return failure_response(
                f"Order already {order.get_status_display()}, cannot update")

        # Enforce status order
        order_flow = ['pending', 'accepted', 'preparing', 'ready']
        if action in ('preparing', 'ready'):
            current_idx = order_flow.index(order.status) \
                if order.status in order_flow else -1
            target_idx = order_flow.index(new_status)
            if target_idx <= current_idx:
                return failure_response(
                    "Invalid status transition")

        order.status = new_status
        if action == 'accept':
            order.accepted_at = timezone.now()
        order.save()
        order.add_status_log(new_status, changed_by=request.user)

        # When ready -> notify available riders (task already exists)
        if action == 'ready' and hasattr(order, 'delivery_task'):
            task = order.delivery_task
            if task.status == 'available':
                task.status = 'available'
                task.save()

        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type=f'order_{action}')

        return success_response(
            f"Order {action}d", OrderSerializer(order).data)
