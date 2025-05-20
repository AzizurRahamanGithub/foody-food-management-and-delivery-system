from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.authentication import TokenAuthentication

class CustomPagination(PageNumberPagination):
    page_size = 10  
    page_size_query_param = 'page_size'
    max_page_size = 100 

class BaseAPIView(APIView):
    permission_classes = [AllowAny]  
    authentication_classes = [TokenAuthentication]  

    def __init__(self, model, serializer_class, *args, **kwargs):
        """
        Initialize with model and serializer_class.
        """
        super().__init__(*args, **kwargs)
        self.model = model
        self.serializer_class = serializer_class

    def success_response(self, message, data, status_code=status.HTTP_200_OK):
        """ Helper method to return a standard success response """
        return Response({
            "success": True,
            "statusCode": status_code,
            "message": message,
            "data": data
        }, status=status_code)

    def failure_response(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        """ Helper method to return a standard failure response """
        return Response({
            "success": False,
            "statusCode": status_code,
            "message": message
        }, status=status_code)

    def get_queryset(self):
        """ Retrieve all objects of the model """
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        """ Get all records (List View) """
        try:
            queryset = self.get_queryset()
            paginator = CustomPagination()
            page = paginator.paginate_queryset(queryset, request)

            # Serialize the data
            serializer = self.serializer_class(page, many=True)

            return paginator.get_paginated_response({
                "success": True,
                "statusCode": 200,
                "message": f"All {self.model._meta.verbose_name_plural}",
                "data": {
                    "count": queryset.count(),
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": serializer.data
                }
            })

        except Exception :
            return self.failure_response("Failed to fetch data.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """ Get a single record (Retrieve View) """
        try:
            obj = self.model.objects.get(id=kwargs['pk'])
            serializer = self.serializer_class(obj)
            return self.success_response(f"{self.model._meta.verbose_name} retrieved successfully.", serializer.data, status.HTTP_200_OK)

        except self.model.DoesNotExist:
            return self.failure_response(f"{self.model._meta.verbose_name} not found.", status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return self.failure_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """ Create a new resource """
        try:
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return self.success_response(f"{self.model._meta.verbose_name} created successfully.", serializer.data, status.HTTP_201_CREATED)
            return self.failure_response("Invalid data.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return self.failure_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, *args, **kwargs):
        """ Partially update a resource """
        try:
            obj = self.model.objects.get(id=kwargs['pk'])
            serializer = self.serializer_class(obj, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return self.success_response(f"{self.model._meta.verbose_name} updated successfully.", serializer.data)
            return self.failure_response("Invalid data.", serializer.errors, status.HTTP_400_BAD_REQUEST)

        except self.model.DoesNotExist:
            return self.failure_response(f"{self.model._meta.verbose_name} not found.", status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return self.failure_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, *args, **kwargs):
        """ Delete a resource """
        try:
            obj = self.model.objects.get(id=kwargs['pk'])
            obj.delete()
            return self.success_response(f"{self.model._meta.verbose_name} deleted successfully.", {}, status.HTTP_204_NO_CONTENT)

        except self.model.DoesNotExist:
            return self.failure_response(f"{self.model._meta.verbose_name} not found.", status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return self.failure_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)