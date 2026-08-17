from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from apps.core.response import success_response, failure_response
from apps.core.pagination import CustomPagination
from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        total_count = queryset.count()
        unread_count = queryset.filter(is_read=False).count()
        read_count = queryset.filter(is_read=True).count()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(
                serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            paginated_data = {"results": serializer.data}

        paginated_data.update({
            "total_count": total_count,
            "unread_count": unread_count,
            "read_count": read_count,
        })
        return Response(paginated_data)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = Notification.objects.filter(
            user=request.user, is_read=False).count()
        return success_response("Unread count", {"unread_count": count})


class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        notif = Notification.objects.filter(
            user=request.user, pk=pk).first()
        if not notif:
            return failure_response("Notification not found",
                                    status.HTTP_404_NOT_FOUND)
        notif.is_read = True
        notif.save(update_fields=['is_read'])
        return success_response("Marked as read", {
            "id": notif.id, "is_read": True})


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        updated = Notification.objects.filter(
            user=request.user, is_read=False).update(is_read=True)
        return success_response(
            "All marked as read",
            {"updated_count": updated})
