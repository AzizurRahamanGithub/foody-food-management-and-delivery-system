from rest_framework import generics
from .models import Notification
from .serializers import NotificationSerializer
from ..core.response import success_response, failure_response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..core.pagination import CustomPagination
from rest_framework.response import Response


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    pagination_class = CustomPagination 

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        # Stats
        total_count = queryset.count()
        unread_count = queryset.filter(is_read=False).count()
        read_count = queryset.filter(is_read=True).count()

        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated_data = self.get_paginated_response(serializer.data).data
        else:
            serializer = self.get_serializer(queryset, many=True)
            paginated_data = {"results": serializer.data}

        # Add stats to the paginated response
        paginated_data.update({
            "total_count": total_count,
            "unread_count": unread_count,
            "read_count": read_count
        })

        return Response(paginated_data)

    
class MarkAllNotificationsReadView(APIView):

    def patch(self, request):
        user = request.user
        updated_count = Notification.objects.filter(
            user=user, is_read=False).update(is_read=True)
        return success_response(
            'Notifications marked as read successfully',
            {'updated_count': updated_count},
            status.HTTP_200_OK
        )
    
    

