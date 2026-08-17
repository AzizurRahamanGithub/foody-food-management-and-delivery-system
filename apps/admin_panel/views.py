from datetime import time, timedelta
from rest_framework import status, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Sum, Count, Avg, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.core.response import success_response, failure_response
from apps.core.crud import DynamicModelViewSet
from apps.auths.models import CustomUser
from apps.merchant.models import (MerchantProfile, GlobalCategory,
                                  MerchantVerification, Category,
                                  MenuItem, Offer)
from apps.rider.models import RiderProfile, RiderDocument
from apps.orders.models import Order, DeliveryTask, Review
from .models import DeliveryZone, PricingRule
from .serializers import DeliveryZoneSerializer, PricingRuleSerializer
from apps.merchant.serializers import (GlobalCategorySerializer,
                                       MerchantVerificationAdminSerializer,
                                       MerchantProfileSerializer)


class AdminPermission(IsAdminUser):
    pass


class GlobalCategoryViewSet(DynamicModelViewSet):
    serializer_class = GlobalCategorySerializer
    permission_classes = [IsAdminUser]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = GlobalCategory
        kwargs['serializer_class'] = GlobalCategorySerializer
        kwargs['item_name'] = 'GlobalCategory'
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        qs = GlobalCategory.objects.all()
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(name__icontains=search)
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(
                is_active=is_active.lower() in ('true', '1', 'yes'))
        return qs


class DeliveryZoneViewSet(DynamicModelViewSet):
    serializer_class = DeliveryZoneSerializer
    permission_classes = [IsAdminUser]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = DeliveryZone
        kwargs['serializer_class'] = DeliveryZoneSerializer
        kwargs['item_name'] = 'DeliveryZone'
        super().__init__(*args, **kwargs)


class PricingRuleViewSet(DynamicModelViewSet):
    serializer_class = PricingRuleSerializer
    permission_classes = [IsAdminUser]

    def __init__(self, *args, **kwargs):
        kwargs['model'] = PricingRule
        kwargs['serializer_class'] = PricingRuleSerializer
        kwargs['item_name'] = 'PricingRule'
        super().__init__(*args, **kwargs)


class AdminOverviewView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        today_start = timezone.make_aware(
            timezone.datetime.combine(now.date(), time.min))
        week_start = today_start - timedelta(days=today_start.weekday())

        orders = Order.objects
        delivered = orders.filter(status='delivered')

        data = {
            "revenue": {
                "total": float(delivered.aggregate(
                    s=Sum('total'))['s'] or 0),
                "today": float(delivered.filter(
                    delivered_at__gte=today_start).aggregate(
                    s=Sum('total'))['s'] or 0),
                "this_week": float(delivered.filter(
                    delivered_at__gte=week_start).aggregate(
                    s=Sum('total'))['s'] or 0),
            },
            "orders": {
                "total": orders.count(),
                "today": orders.filter(
                    placed_at__gte=today_start).count(),
                "pending": orders.filter(status='pending').count(),
                "delivered": delivered.count(),
                "cancelled": orders.filter(status='cancelled').count(),
                "by_status": dict(
                    Order.objects.values_list('status').annotate(
                        c=Count('id'))),
            },
            "customers": {
                "total": CustomUser.objects.filter(
                    role='customer').count(),
                "active": CustomUser.objects.filter(
                    role='customer', is_active=True).count(),
            },
            "merchants": {
                "total": MerchantProfile.objects.count(),
                "approved": MerchantProfile.objects.filter(
                    verification_status='approved').count(),
                "pending": MerchantProfile.objects.filter(
                    verification_status='pending').count(),
            },
            "riders": {
                "total": RiderProfile.objects.count(),
                "online": RiderProfile.objects.filter(
                    is_online=True).count(),
                "pending_documents": RiderDocument.objects.filter(
                    status='pending').count(),
            },
            "live_operations": {
                "preparing": orders.filter(status='preparing').count(),
                "ready": orders.filter(status='ready').count(),
                "picked_up": orders.filter(status='picked_up').count(),
            },
            "reviews": {
                "avg_rating": float(Review.objects.aggregate(
                    a=Avg('rating'))['a'] or 0),
                "total": Review.objects.count(),
            },
        }
        return success_response("Overview", data)


class AdminOrdersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status')
        date_from = request.query_params.get('from')
        date_to = request.query_params.get('to')
        qs = Order.objects.all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        if date_from:
            qs = qs.filter(placed_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(placed_at__date__lte=date_to)
        from apps.orders.serializers import OrderSerializer
        return success_response(
            "Orders", OrderSerializer(qs, many=True).data)


class AdminOrderDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        from apps.orders.serializers import OrderSerializer
        order = get_object_or_404(Order, pk=pk)
        return success_response(
            "Order details", OrderSerializer(order).data)


class AdminMerchantView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        status_filter = request.query_params.get('status')
        search = request.query_params.get('search')
        qs = MerchantProfile.objects.all()
        if status_filter:
            qs = qs.filter(verification_status=status_filter)
        if search:
            qs = qs.filter(
                Q(business_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(manager_name__icontains=search))
        return success_response(
            "Merchants",
            MerchantProfileSerializer(qs, many=True).data)

    def post(self, request, pk=None):
        if not pk:
            return failure_response("Merchant id required")
        merchant = get_object_or_404(MerchantProfile, pk=pk)
        action = request.data.get('action')
        if action not in ('approve', 'reject'):
            return failure_response("Invalid action")
        merchant.verification_status = (
            MerchantProfile.VerificationStatus.APPROVED
            if action == 'approve'
            else MerchantProfile.VerificationStatus.REJECTED)
        merchant.save()
        return success_response(
            f"Merchant {action}d", {
                "id": merchant.id,
                "verification_status": merchant.verification_status})


class AdminMerchantVerificationView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, pk=None):
        if pk:
            verification = get_object_or_404(MerchantVerification, pk=pk)
            return success_response(
                "Verification details",
                MerchantVerificationAdminSerializer(verification).data)

        status_filter = request.query_params.get('status', 'pending')
        qs = MerchantVerification.objects.select_related(
            'merchant', 'merchant__user').all()
        if status_filter:
            qs = qs.filter(status=status_filter)
        return success_response(
            "Verifications",
            MerchantVerificationAdminSerializer(qs, many=True).data)

    def post(self, request, pk):
        verification = get_object_or_404(MerchantVerification, pk=pk)
        action = request.data.get('action')

        if action not in ('approve', 'reject'):
            return failure_response("Invalid action")

        if action == 'reject':
            reason = request.data.get('reason', '')
            if not reason:
                return failure_response(
                    "Rejection reason is required")
            verification.status = 'rejected'
            verification.rejection_reason = reason
            verification.merchant.verification_status = 'rejected'
        else:
            verification.status = 'approved'
            verification.rejection_reason = ''
            verification.merchant.verification_status = 'approved'

        verification.reviewed_by = request.user
        verification.reviewed_at = timezone.now()
        verification.save()
        verification.merchant.save()

        return success_response(
            f"Verification {action}d", {
                "id": verification.id,
                "status": verification.status,
                "merchant_verification_status":
                    verification.merchant.verification_status})


class AdminRiderView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        qs = RiderProfile.objects.all()
        from apps.rider.serializers import RiderProfileSerializer
        return success_response(
            "Riders", RiderProfileSerializer(qs, many=True).data)

    def post(self, request, pk=None):
        if not pk:
            return failure_response("Rider id required")
        rider = get_object_or_404(RiderProfile, pk=pk)
        action = request.data.get('action')
        if action == 'verify':
            doc_id = request.data.get('document_id')
            doc = get_object_or_404(RiderDocument, pk=doc_id, rider=rider)
            doc.status = RiderDocument.Status.VERIFIED
            doc.save()
            if rider.documents.exclude(status='verified').count() == 0:
                rider.verification_status = \
                    RiderProfile.VerificationStatus.APPROVED
                rider.save()
            return success_response(
                "Document verified",
                {"document_id": doc.id, "status": doc.status})
        if action == 'reject':
            doc = get_object_or_404(
                RiderDocument, pk=request.data.get('document_id'),
                rider=rider)
            doc.status = RiderDocument.Status.REJECTED
            doc.rejection_reason = request.data.get('reason', '')
            doc.save()
            return success_response(
                "Document rejected",
                {"document_id": doc.id, "status": doc.status})
        if action in ('approve', 'reject'):
            rider.verification_status = (
                RiderProfile.VerificationStatus.APPROVED
                if action == 'approve'
                else RiderProfile.VerificationStatus.REJECTED)
            rider.save()
            return success_response(
                f"Rider {action}d", {
                    "id": rider.id,
                    "verification_status": rider.verification_status})
        return failure_response("Invalid action")


class AdminCustomerView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        customers = CustomUser.objects.filter(role='customer')
        return success_response(
            "Customers",
            [{
                "id": u.id, "full_name": u.full_name, "email": u.email,
                "phone": u.phone_number, "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            } for u in customers])

    def post(self, request, pk=None):
        if not pk:
            return failure_response("Customer id required")
        user = get_object_or_404(CustomUser, pk=pk, role='customer')
        user.is_active = request.data.get('is_active', not user.is_active)
        user.save()
        return success_response(
            "Customer updated",
            {"id": user.id, "is_active": user.is_active})


class AdminAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        now = timezone.now()
        days = int(request.query_params.get('days', 7))
        start = now - timedelta(days=days - 1)
        start = timezone.make_aware(
            timezone.datetime.combine(start.date(), time.min))

        daily = []
        for i in range(days):
            d = start + timedelta(days=i)
            day_end = d + timedelta(days=1)
            day_orders = Order.objects.filter(
                placed_at__gte=d, placed_at__lt=day_end)
            daily.append({
                "date": d.date().isoformat(),
                "orders": day_orders.count(),
                "revenue": float(day_orders.exclude(
                    status__in=['cancelled', 'rejected']).aggregate(
                    s=Sum('total'))['s'] or 0),
            })

        top_merchants = MerchantProfile.objects.annotate(
            order_count=Count('orders')).order_by('-order_count')[:10]

        data = {
            "daily": daily,
            "top_merchants": [{
                "id": m.id, "name": m.business_name,
                "order_count": m.order_count,
            } for m in top_merchants],
        }
        return success_response("Analytics", data)


class AdminReportsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        report_type = request.query_params.get('type', 'summary')
        now = timezone.now()
        month_start = now.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_orders = Order.objects.filter(placed_at__gte=month_start)
        data = {
            "type": report_type,
            "monthly_orders": monthly_orders.count(),
            "monthly_revenue": float(monthly_orders.exclude(
                status__in=['cancelled', 'rejected']).aggregate(
                s=Sum('total'))['s'] or 0),
            "avg_order_value": float(monthly_orders.exclude(
                status__in=['cancelled', 'rejected']).aggregate(
                a=Avg('total'))['a'] or 0),
            "new_merchants_this_month": MerchantProfile.objects.filter(
                created_at__gte=month_start).count(),
            "new_riders_this_month": RiderProfile.objects.filter(
                created_at__gte=month_start).count(),
        }
        return success_response("Reports", data)


class AdminAddRestaurantView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return failure_response("Email required")
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return failure_response(
                "User not found. Register merchant first")
        merchant, created = MerchantProfile.objects.get_or_create(
            user=user)
        serializer = MerchantProfileSerializer(
            merchant, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            merchant.verification_status = \
                MerchantProfile.VerificationStatus.APPROVED
            merchant.save()
            return success_response(
                "Restaurant added",
                MerchantProfileSerializer(merchant).data,
                status.HTTP_201_CREATED if created
                else status.HTTP_200_OK)
        return failure_response("Invalid data", serializer.errors)


class AdminInviteRiderView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return failure_response("Email required")
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            return failure_response(
                "User not found. Register rider first")
        rider, created = RiderProfile.objects.get_or_create(user=user)
        from apps.rider.serializers import RiderProfileSerializer
        serializer = RiderProfileSerializer(
            rider, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response(
                "Rider invited", RiderProfileSerializer(rider).data,
                status.HTTP_201_CREATED if created
                else status.HTTP_200_OK)
        return failure_response("Invalid data", serializer.errors)
