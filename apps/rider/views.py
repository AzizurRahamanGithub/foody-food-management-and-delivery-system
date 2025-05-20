from datetime import time
from decimal import Decimal
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.core.response import success_response, failure_response
from apps.orders.models import Order, DeliveryTask
from apps.orders.serializers import OrderSerializer, DeliveryTaskSerializer
from apps.auths.models import CustomUser
from .models import RiderProfile, RiderDocument, BankInfo, Earning
from .serializers import (RiderProfileSerializer, RiderDocumentSerializer,
                          BankInfoSerializer, EarningSerializer)


class RiderRolePermission(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.role == 'rider'


class RiderProfileView(APIView):
    permission_classes = [RiderRolePermission]

    def get(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        return success_response(
            "Profile fetched", RiderProfileSerializer(profile).data)

    def put(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        serializer = RiderProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return success_response("Profile updated", serializer.data)
        return failure_response("Invalid data", serializer.errors)


class AvailabilityView(APIView):
    permission_classes = [RiderRolePermission]

    def post(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        is_online = request.data.get('is_online')
        if is_online is None:
            return failure_response("'is_online' is required")
        profile.is_online = bool(is_online)
        profile.availability_status = (
            RiderProfile.Availability.ONLINE if profile.is_online
            else RiderProfile.Availability.OFFLINE)
        profile.current_latitude = request.data.get('latitude') or profile.current_latitude
        profile.current_longitude = request.data.get('longitude') or profile.current_longitude
        profile.save()
        return success_response(
            "Availability updated",
            {"is_online": profile.is_online,
             "availability_status": profile.availability_status})


class RiderDocumentView(APIView):
    permission_classes = [RiderRolePermission]

    def get(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        return success_response(
            "Documents fetched",
            RiderDocumentSerializer(profile.documents.all(), many=True).data)

    def post(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        serializer = RiderDocumentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(rider=profile)
            return success_response(
                "Document uploaded", serializer.data, status.HTTP_201_CREATED)
        return failure_response("Invalid data", serializer.errors)

    def delete(self, request, pk=None):
        doc = get_object_or_404(
            RiderDocument, pk=pk, rider__user=request.user)
        doc.delete()
        return success_response("Document deleted")


class BankInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = BankInfo.objects.filter(user=request.user)
        return success_response(
            "Bank info fetched", BankInfoSerializer(info, many=True).data)

    def post(self, request):
        serializer = BankInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return success_response(
                "Bank info saved", serializer.data, status.HTTP_201_CREATED)
        return failure_response("Invalid data", serializer.errors)


class AvailableOrdersView(APIView):
    permission_classes = [RiderRolePermission]

    def get(self, request):
        tasks = DeliveryTask.objects.filter(
            status=DeliveryTask.Status.AVAILABLE,
            order__status=Order.Status.READY).select_related('order')
        data = []
        for t in tasks:
            order_data = OrderSerializer(t.order).data
            order_data['task_id'] = t.id
            order_data['task_status'] = t.status
            order_data['pickup_code_required'] = True
            data.append(order_data)
        return success_response("Available orders", data)


class MyDeliveryTasksView(APIView):
    permission_classes = [RiderRolePermission]

    def get(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        tasks = DeliveryTask.objects.filter(rider=profile).order_by('-id')
        return success_response(
            "Delivery tasks", DeliveryTaskSerializer(tasks, many=True).data)


class AcceptTaskView(APIView):
    permission_classes = [RiderRolePermission]

    def post(self, request, task_id):
        task = get_object_or_404(DeliveryTask, pk=task_id)
        if task.status != DeliveryTask.Status.AVAILABLE:
            return failure_response("This task is no longer available")
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        task.rider = profile
        task.status = DeliveryTask.Status.ACCEPTED
        task.save()
        order = task.order
        order.rider = profile
        order.save()
        order.add_status_log(
            Order.Status.READY, changed_by=request.user,
            note=f"Rider {request.user.full_name} accepted delivery")
        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type='rider_assigned')
        return success_response(
            "Task accepted", DeliveryTaskSerializer(task).data)


class ConfirmPickupView(APIView):
    permission_classes = [RiderRolePermission]

    def post(self, request, task_id):
        task = get_object_or_404(
            DeliveryTask, pk=task_id, rider__user=request.user)
        if task.status != DeliveryTask.Status.ACCEPTED:
            return failure_response("Task is not in accepted state")
        code = request.data.get('pickup_code')
        if not code or str(code) != str(task.pickup_code):
            return failure_response("Invalid pickup code")
        order = task.order
        task.status = DeliveryTask.Status.PICKED_UP
        task.picked_up_at = timezone.now()
        task.save()
        order.status = Order.Status.PICKED_UP
        order.save()
        order.add_status_log(
            Order.Status.PICKED_UP, changed_by=request.user,
            note="Items picked up by rider")
        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type='order_picked_up')
        return success_response(
            "Pickup confirmed", DeliveryTaskSerializer(task).data)


class MarkDeliveredView(APIView):
    permission_classes = [RiderRolePermission]

    def post(self, request, task_id):
        task = get_object_or_404(
            DeliveryTask, pk=task_id, rider__user=request.user)
        if task.status != DeliveryTask.Status.PICKED_UP:
            return failure_response("Task is not in picked-up state")
        order = task.order
        task.status = DeliveryTask.Status.DELIVERED
        task.delivered_at = timezone.now()
        task.save()
        order.status = Order.Status.DELIVERED
        order.delivered_at = timezone.now()
        order.payment_status = Order.PaymentStatus.PAID if \
            order.payment_method != Order.PaymentMethod.CASH_ON_DELIVERY \
            else order.payment_status
        order.save()
        order.add_status_log(
            Order.Status.DELIVERED, changed_by=request.user,
            note="Order delivered")

        Earning.objects.create(
            rider=order.rider, order=order,
            earning_type=Earning.EarningType.DELIVERY_FEE,
            amount=order.delivery_fee,
            description=f"Delivery fee for {order.order_number}")

        from apps.orders.tracking import broadcast_order_update
        broadcast_order_update(order, event_type='order_delivered')

        return success_response(
            "Order delivered", DeliveryTaskSerializer(task).data)


class EarningsView(APIView):
    permission_classes = [RiderRolePermission]

    def get(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        now = timezone.now()
        today_start = timezone.make_aware(
            timezone.datetime.combine(now.date(), time.min))
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        earnings = profile.earnings

        def agg(qs):
            return float(qs.aggregate(total=Sum('amount'))['total'] or 0)

        data = {
            "today": {
                "total": agg(earnings.filter(created_at__gte=today_start)),
                "deliveries": earnings.filter(
                    created_at__gte=today_start).count(),
            },
            "this_week": {
                "total": agg(earnings.filter(created_at__gte=week_start)),
                "deliveries": earnings.filter(
                    created_at__gte=week_start).count(),
            },
            "this_month": {
                "total": agg(earnings.filter(created_at__gte=month_start)),
                "deliveries": earnings.filter(
                    created_at__gte=month_start).count(),
            },
            "lifetime": {
                "total": agg(earnings),
                "deliveries": earnings.count(),
            },
        }
        return success_response("Earning overview", data)


class EarningsHistoryView(APIView):
    permission_classes = [RiderRolePermission]

    def get(self, request):
        profile, _ = RiderProfile.objects.get_or_create(user=request.user)
        period = request.query_params.get('period', 'all')
        qs = profile.earnings.all()
        now = timezone.now()
        if period == 'day':
            start = timezone.make_aware(
                timezone.datetime.combine(now.date(), time.min))
            qs = qs.filter(created_at__gte=start)
        elif period == 'week':
            start = timezone.make_aware(
                timezone.datetime.combine(now.date(), time.min))
            start = start - timedelta(days=start.weekday())
            qs = qs.filter(created_at__gte=start)
        elif period == 'month':
            start = now.replace(day=1, hour=0, minute=0,
                                second=0, microsecond=0)
            qs = qs.filter(created_at__gte=start)
        return success_response(
            "Earning history", EarningSerializer(qs, many=True).data)
