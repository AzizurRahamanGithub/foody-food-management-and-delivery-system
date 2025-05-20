from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination
from rest_framework.authentication import TokenAuthentication
from rest_framework import status

class CustomPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class BasePublicAPIView(APIView):
    """
    Base API View that can be used for any model with a specific serializer.
    It handles listing (GET) and retrieving (RETRIEVE) actions for any model.
    """
    permission_classes = [AllowAny]  
    authentication_classes = [TokenAuthentication]  

    def __init__(self, model, serializer_class, *args, **kwargs):
        """
        Initialize with model and serializer_class.
        """
        super().__init__(*args, **kwargs)
        self.model = model
        self.serializer_class = serializer_class

    def get_queryset(self):
        """ Retrieve all objects of the model """
        return self.model.objects.all()

    def get(self, request, *args, **kwargs):
        """ Handle both list and retrieve based on whether pk is provided """
        # Check if pk is provided in URL
        if 'pk' in kwargs:
            return self.retrieve(request, *args, **kwargs)
        else:
            return self.list(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        """ Get all records (List View) """
        try:
            queryset = self.get_queryset()
            paginator = CustomPagination()
            page = paginator.paginate_queryset(queryset, request)    
            serializer = self.serializer_class(page, many=True)

            response_data = {
                "success": True,
                "statusCode": 200,
                "message": f"All {self.model._meta.verbose_name_plural}",
                "data": {
                    "count": queryset.count(),
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": serializer.data
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception :
            return self.failure_response("Failed to fetch data.", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """ Get a single record (Retrieve View) """
        try:
            obj = self.model.objects.get(id=kwargs['pk'])  # Get the object by pk
            serializer = self.serializer_class(obj)
            response_data = {
                "success": True,
                "statusCode": 200,
                "message": f"{self.model._meta.verbose_name} retrieved successfully.",
                "data": serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except self.model.DoesNotExist:
            return self.failure_response(f"{self.model._meta.verbose_name} not found.", status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return self.failure_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)

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


# from .models import Podcast
# from .serializers import PodCastSerializer

# class PublicPodcastsAPIView(BasePublicAPIView):
#     def __init__(self, *args, **kwargs):
#         super().__init__(model=Podcast, serializer_class=PodCastSerializer, *args, **kwargs)


# from django.urls import path
# from .views import PublicPodcastsAPIView

# urlpatterns = [
#     path('public/podcasts/', PublicPodcastsAPIView.as_view(), name='public-podcasts-list'),
#     path('public/podcasts/<int:pk>/', PublicPodcastsAPIView.as_view(), name='public-podcasts-detail'),
# ]