

from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    
class MultipleFileUploadSerializer(serializers.Serializer):
   files = serializers.ListField(child=serializers.FileField(), required=True)
        