from rest_framework import generics
from rest_framework.response import Response

class BaseListAPIView(generics.ListAPIView):
    pagination_class = None  # default, can override in child

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        # auto-generate success message based on model name
        model_name = queryset.model.__name__  # e.g., "Package"
        success_message = f"All {model_name.lower()}s fetched successfully"

        return Response({
            "success": True,
            "statusCode": 200,
            "message": success_message,
            "data": serializer.data
        })



# class AllPackageList(BaseListAPIView):
#     queryset = Package.objects.all().order_by('-id')
#     serializer_class = PackageSerializer
