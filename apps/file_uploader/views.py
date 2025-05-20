from rest_framework import status
from rest_framework.views import APIView
from .serializers import FileUploadSerializer, MultipleFileUploadSerializer
from .upload_utils import upload_file_to_digital_ocean, delete_file_from_digital_ocean
from apps.core.response import failure_response, success_response


class FileUploadView(APIView):
    """
    Handle file upload (image or video) to DigitalOcean Spaces.
    It will handle the file upload and return the public URL.
    """

    def post(self, request, *args, **kwargs):
        """Upload a new file (image or video)"""
        serializer = FileUploadSerializer(data=request.data)
        if serializer.is_valid():
            file = request.FILES['file']
            try:
                file_url = upload_file_to_digital_ocean(file)
                return success_response("File uploaded successfully", {"file_url": file_url}, status=status.HTTP_200_OK)
            except Exception as e:
                return failure_response(str(e), {}, status=status.HTTP_400_BAD_REQUEST)

        return failure_response("Invalid data.", serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FileDeleteView(APIView):
    """
    Handle file deletion from DigitalOcean Spaces.
    It will remove the file based on the given URL or file name.
    """

    def post(self, request, *args, **kwargs):
        file_url = request.data.get('file_url', None)
        if not file_url:
            return failure_response("File URL is required.", {}, status=status.HTTP_400_BAD_REQUEST)
        try:
            delete_file_from_digital_ocean(file_url)
            return success_response("File deleted successfully", {}, status=status.HTTP_200_OK)
        except Exception as e:
            return failure_response(str(e), {}, status=status.HTTP_400_BAD_REQUEST)


class MultipleFileUploadView(APIView):
    """
    Handle multiple file uploads (image or video) to DigitalOcean Spaces.
    It will handle the file uploads and return the public URLs.
    """

    def post(self, request, *args, **kwargs):
        """Upload multiple files (images or videos)"""
        serializer = MultipleFileUploadSerializer(data=request.data)
        if serializer.is_valid():
            files = request.FILES.getlist('files')
            file_urls = []

            for file in files:
                try:
                    file_url = upload_file_to_digital_ocean(file)
                    file_urls.append(file_url)
                except Exception as e:
                    return failure_response(str(e), {}, status=status.HTTP_400_BAD_REQUEST)
            return success_response("Files uploaded successfully", {"file_urls": file_urls}, status=status.HTTP_200_OK)

        return failure_response("Invalid data.", serializer.errors, status=status.HTTP_400_BAD_REQUEST)
