from django.urls import path
from .views import FileUploadView, FileDeleteView,MultipleFileUploadView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('delete/', FileDeleteView.as_view(), name='file-delete'),
    path('multiple/file/',MultipleFileUploadView.as_view(),name="multiple-file")
    #  path('upload/cloudinary/', FileUploaderToCloudinary.as_view(), name='file_upload_cloudinary'),
]