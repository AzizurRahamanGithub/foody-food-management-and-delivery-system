from rest_framework import viewsets, status
# from rest_framework.permissions import 
from .response import success_response, failure_response

class DynamicModelViewSet(viewsets.ModelViewSet):
    """
    Generic CRUD for any model with automatic user assignment.
    Now supports perform_create and perform_update hooks.
    """
    # permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        self.model = kwargs.pop('model', None)
        self.serializer_class = kwargs.pop('serializer_class', None)
        self.item_name = kwargs.pop('item_name', None)
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        return self.model.objects.all().order_by('-id')

    # ✅ list remains same
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            serializer = self.serializer_class(queryset, many=True)
            return success_response(f"All {self.item_name}s fetched successfully.", serializer.data, status.HTTP_200_OK)
        except Exception as e:
            return failure_response(f"Failed to fetch {self.item_name}s.", {"detail": str(e)})

    # ✅ create now triggers perform_create()
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        if serializer.is_valid():
            instance = self.perform_create(serializer)
            return success_response(f"{self.item_name} created successfully.", self.serializer_class(instance).data, status.HTTP_201_CREATED)
        else:
            return failure_response("Invalid data.", serializer.errors, status.HTTP_400_BAD_REQUEST)

    def perform_create(self, serializer):
        """Default behavior with user auto-assign support"""
        if hasattr(self.model, 'user'):
            return serializer.save(user=self.request.user)
        return serializer.save()

    # ✅ retrieve same
    def retrieve(self, request, *args, **kwargs):
        try:
            item = self.model.objects.get(pk=kwargs.get('pk'))
            serializer = self.serializer_class(item)
            return success_response(f"{self.item_name} details fetched successfully.", serializer.data, status.HTTP_200_OK)
        except self.model.DoesNotExist:
            return failure_response(f"{self.item_name} not found.", status.HTTP_404_NOT_FOUND)

    # ✅ update now triggers perform_update()
    def update(self, request, *args, **kwargs):
        try:
            item = self.model.objects.get(pk=kwargs.get('pk'))
            serializer = self.serializer_class(item, data=request.data, partial=True)
            if serializer.is_valid():
                instance = self.perform_update(serializer)
                return success_response(f"{self.item_name} updated successfully.", self.serializer_class(instance).data, status.HTTP_200_OK)
            return failure_response("Invalid data.", serializer.errors, status.HTTP_400_BAD_REQUEST)
        except self.model.DoesNotExist:
            return failure_response(f"{self.item_name} not found.", status.HTTP_404_NOT_FOUND)

    def perform_update(self, serializer):
        return serializer.save()

    # ✅ destroy same
    def destroy(self, request, *args, **kwargs):
        try:
            item = self.model.objects.get(pk=kwargs.get('pk'))
            item.delete()
            return success_response(f"{self.item_name} deleted successfully.", {}, status.HTTP_204_NO_CONTENT)
        except self.model.DoesNotExist:
            return failure_response(f"{self.item_name} not found.", status.HTTP_404_NOT_FOUND)
