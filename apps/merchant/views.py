from datetime import time
from rest_framework import status, viewsets, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import timedelta
from apps.core.response import success_response, failure_response
from apps.core.crud import DynamicModelViewSet
from .models import (MerchantProfile, GlobalCategory, MerchantSchedule,
                     MerchantVerification, Category, MenuItem,
                     AddonGroup, Addon, Offer, ItemReview)
from .serializers import (MerchantProfileSerializer, GlobalCategorySerializer,
                          MerchantScheduleSerializer,
                          MerchantVerificationSerializer,
                          CategorySerializer, MenuItemSerializer,
                          MenuItemListSerializer, MenuItemDetailSerializer,
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
                "Profile fetched successfully",
                MerchantProfileSerializer(profile).data)
        except MerchantProfile.DoesNotExist:
            return failure_response(
                "Merchant profile not found",
                status=status.HTTP_404_NOT_FOUND)

    def put(self, request):
        try:
            profile = MerchantProfile.objects.get(user=request.user)
        except MerchantProfile.DoesNotExist:
            return failure_response(
                "Merchant profile not found",
                status=status.HTTP_404_NOT_FOUND)

        schedule_data = request.data.pop('schedule', None)
        serializer = MerchantProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if schedule_data is not None:
                self._update_schedule(profile, schedule_data)
            profile.refresh_from_db()
            return success_response(
                "Profile updated successfully",
                MerchantProfileSerializer(profile).data)
        return failure_response("Invalid data", serializer.errors)

    def post(self, request):
        try:
            profile, created = MerchantProfile.objects.get_or_create(
                user=request.user)
        except Exception as e:
            return failure_response("Profile setup failed", str(e))

        schedule_data = request.data.pop('schedule', None)
        serializer = MerchantProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if schedule_data is not None:
                self._update_schedule(profile, schedule_data)
            profile.refresh_from_db()
            return success_response(
                "Profile setup completed",
                MerchantProfileSerializer(profile).data,
                status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return failure_response("Invalid data", serializer.errors)

    def _update_schedule(self, profile, schedule_list):
        for item in schedule_list:
            day = item.get('day_of_week')
            if day is None:
                continue
            is_open = item.get('is_open', True)
            opening_time = item.get('opening_time')
            closing_time = item.get('closing_time')
            MerchantSchedule.objects.update_or_create(
                merchant=profile, day_of_week=day,
                defaults={
                    'is_open': is_open,
                    'opening_time': opening_time,
                    'closing_time': closing_time,
                })


class GlobalCategoryListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search = request.query_params.get('search', '')
        qs = GlobalCategory.objects.filter(is_active=True)
        if search:
            qs = qs.filter(name__icontains=search)
        return success_response(
            "Categories",
            GlobalCategorySerializer(qs, many=True).data)


class MerchantVerifyView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request):
        try:
            profile = MerchantProfile.objects.get(user=request.user)
        except MerchantProfile.DoesNotExist:
            return failure_response(
                "Merchant profile not found",
                status=status.HTTP_404_NOT_FOUND)
        try:
            verification = MerchantVerification.objects.get(merchant=profile)
            return success_response(
                "Verification status",
                MerchantVerificationSerializer(verification).data)
        except MerchantVerification.DoesNotExist:
            return success_response(
                "No verification submitted yet", {})

    def post(self, request):
        try:
            profile = MerchantProfile.objects.get(user=request.user)
        except MerchantProfile.DoesNotExist:
            return failure_response(
                "Merchant profile not found",
                status=status.HTTP_404_NOT_FOUND)

        verification, created = MerchantVerification.objects.get_or_create(
            merchant=profile)

        if verification.status == 'approved':
            return failure_response(
                "Verification already approved")

        serializer = MerchantVerificationSerializer(
            verification, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save(status='pending', rejection_reason='')
            profile.verification_status = 'pending'
            profile.save()
            return success_response(
                "Verification submitted",
                MerchantVerificationSerializer(verification).data,
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

    def get_serializer_class(self):
        if self.action == 'list':
            return MenuItemListSerializer
        return MenuItemSerializer

    def get_queryset(self):
        qs = MenuItem.objects.filter(merchant__user=self.request.user)

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category_id=category)

        is_available = self.request.query_params.get('is_available')
        if is_available is not None:
            qs = qs.filter(
                is_available=is_available.lower() in ('true', '1', 'yes'))

        is_veg = self.request.query_params.get('is_veg')
        if is_veg is not None:
            qs = qs.filter(is_veg=is_veg.lower() in ('true', '1', 'yes'))

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search))

        min_price = self.request.query_params.get('min_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)

        max_price = self.request.query_params.get('max_price')
        if max_price:
            qs = qs.filter(price__lte=max_price)

        ordering = self.request.query_params.get('ordering')
        if ordering:
            allowed = ['price', '-price', 'rating', '-rating',
                       'name', '-name', 'preparation_time_min',
                       '-preparation_time_min']
            if ordering in allowed:
                qs = qs.order_by(ordering)

        top_rated = self.request.query_params.get('top_rated')
        if top_rated and top_rated.lower() in ('true', '1', 'yes'):
            qs = qs.order_by('-rating')

        return qs

    def perform_create(self, serializer):
        merchant = MerchantProfile.objects.get(user=self.request.user)
        return serializer.save(merchant=merchant)


class MerchantItemsListView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request):
        merchant = MerchantProfile.objects.get(user=request.user)
        items = MenuItem.objects.filter(
            merchant=merchant, is_available=True
        ).values('id', 'name', 'price')
        return success_response("Items", list(items))


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

    def get_queryset(self):
        return Addon.objects.filter(
            group__merchant__user=self.request.user)


class ItemAddonManageView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request, item_id):
        item = get_object_or_404(
            MenuItem, pk=item_id,
            merchant__user=request.user)
        groups = AddonGroup.objects.filter(
            item_groups__item=item
        ).prefetch_related('addons').order_by('name')
        return success_response(
            "Item addon groups",
            AddonGroupSerializer(groups, many=True).data)

    def post(self, request, item_id):
        item = get_object_or_404(
            MenuItem, pk=item_id,
            merchant__user=request.user)
        merchant = MerchantProfile.objects.get(
            user=request.user)

        group_name = request.data.get('group_name', '').strip()
        if not group_name:
            return failure_response("group_name is required")

        group, created = AddonGroup.objects.get_or_create(
            merchant=merchant,
            name=group_name,
            defaults={
                'is_required': request.data.get(
                    'is_required', False),
                'is_multiple_choice': request.data.get(
                    'is_multiple_choice', True),
                'max_selectable': request.data.get(
                    'max_selectable', 0),
            })

        if not created:
            group.is_required = request.data.get(
                'is_required', group.is_required)
            group.is_multiple_choice = request.data.get(
                'is_multiple_choice', group.is_multiple_choice)
            group.max_selectable = request.data.get(
                'max_selectable', group.max_selectable)
            group.save()

        MenuItemAddon.objects.get_or_create(
            item=item, group=group)

        addons_data = request.data.get('addons', [])
        created_addons = []
        for ad in addons_data:
            addon, _ = Addon.objects.update_or_create(
                group=group,
                name=ad.get('name', '').strip(),
                defaults={
                    'price': ad.get('price', 0),
                    'size': ad.get('size', ''),
                    'is_available': ad.get('is_available', True),
                })
            created_addons.append(addon)

        return success_response(
            "Addon group saved",
            AddonGroupSerializer(group).data,
            status.HTTP_201_CREATED)


class ItemAddonDeleteView(APIView):
    permission_classes = [MerchantRolePermission]

    def delete(self, request, item_id, group_id):
        item = get_object_or_404(
            MenuItem, pk=item_id,
            merchant__user=request.user)
        MenuItemAddon.objects.filter(
            item=item, group_id=group_id).delete()
        AddonGroup.objects.filter(
            pk=group_id,
            merchant__user=request.user).delete()
        return success_response("Addon group removed")


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            instance = self.perform_create(serializer)
            return Response(
                {
                    "success": True,
                    "status_code": status.HTTP_201_CREATED,
                    "message": "Offer created successfully.",
                    "data": OfferSerializer(
                        instance, context={'request': request}).data
                }, status=status.HTTP_201_CREATED)
        return failure_response("Invalid data.", serializer.errors)

    def update(self, request, *args, **kwargs):
        try:
            item = Offer.objects.get(pk=kwargs.get('pk'))
        except Offer.DoesNotExist:
            return failure_response("Offer not found.",
                                    status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(
            item, data=request.data, partial=True)
        if serializer.is_valid():
            instance = serializer.save()
            return success_response(
                "Offer updated successfully.",
                OfferSerializer(
                    instance, context={'request': request}).data)
        return failure_response("Invalid data.", serializer.errors)


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
            "active_items": merchant.menu_items.filter(
                is_available=True).count(),
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
            return failure_response(
                "Order not found", status=status.HTTP_404_NOT_FOUND)
        return success_response("Order details", OrderSerializer(order).data)


class MerchantOrderStatusView(APIView):
    permission_classes = [MerchantRolePermission]

    def post(self, request, pk):
        from apps.orders.models import Order
        from apps.orders.serializers import OrderSerializer
        merchant = MerchantProfile.objects.get(user=request.user)
        order = merchant.orders.filter(pk=pk).first()
        if not order:
            return failure_response(
                "Order not found", status=status.HTTP_404_NOT_FOUND)

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
                f"Order already {order.get_status_display()}, "
                "cannot update")

        order_flow = ['pending', 'accepted', 'preparing', 'ready']
        if action in ('preparing', 'ready'):
            current_idx = order_flow.index(order.status) \
                if order.status in order_flow else -1
            target_idx = order_flow.index(new_status)
            if target_idx <= current_idx:
                return failure_response("Invalid status transition")

        order.status = new_status
        if action == 'accept':
            order.accepted_at = timezone.now()
        order.save()
        order.add_status_log(new_status, changed_by=request.user)

        if action == 'ready' and hasattr(order, 'delivery_task'):
            task = order.delivery_task
            if task.status == 'available':
                task.status = 'available'
                task.save()

        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type=f'order_{action}')

        from apps.notification.utils import (
            notify_order_confirmed,
            notify_order_preparing)
        if action == 'accept':
            notify_order_confirmed(order.customer, order)
        elif action == 'preparing':
            notify_order_preparing(order.customer, order)

        return success_response(
            f"Order {action}d", OrderSerializer(order).data)


class MerchantItemReviewsView(APIView):
    permission_classes = [MerchantRolePermission]

    def get(self, request):
        merchant = MerchantProfile.objects.get(user=request.user)
        item_id = request.query_params.get('item_id')
        reviews = ItemReview.objects.filter(
            item__merchant=merchant).select_related(
            'item', 'customer').order_by('-created_at')

        if item_id:
            reviews = reviews.filter(item_id=item_id)

        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        total = reviews.count()

        from .serializers import ItemReviewSerializer
        return success_response("Item reviews", {
            "average_rating": round(float(avg_rating), 2),
            "total_reviews": total,
            "reviews": ItemReviewSerializer(reviews, many=True).data,
        })
