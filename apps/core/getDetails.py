from rest_framework import generics
from rest_framework.response import Response

class BaseRetrieveAPIView(generics.RetrieveAPIView):
    """
    Base class for retrieve-only endpoints.
    Automatically generates success message based on model name.
    """
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        model_name = instance.__class__.__name__
        success_message = f"{model_name} fetched successfully"

        return Response({
            "success": True,
            "statusCode": 200,
            "message": success_message,
            "data": serializer.data
        })


# class PackageRetrieveView(BaseRetrieveAPIView):
#     queryset = Package.objects.all()
#     serializer_class = PackageSerializer