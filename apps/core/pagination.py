from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import status


class CustomPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'  
    max_page_size = 100  


class BasePaginatedViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination  

    def get_paginated_response(self, serializer):
        """Override this method to provide consistent pagination response."""
        return Response({
            "success": True,
            "statusCode": status.HTTP_200_OK,
            "message": "Paginated list",
            "data": serializer.data,
            "pagination": {
                "count": self.paginator.page.paginator.count,  
                "next": self.paginator.get_next_link(),  
                "previous": self.paginator.get_previous_link(),  
            }
        })