# from django import forms
# from django.contrib import admin
# from .models import UploadedFile
# from .upload_utils import upload_file_to_digital_ocean, upload_video_to_digital_ocean  # তোমার uploader ফাইলের নাম ধরে নিচ্ছি upload_to_spaces.py

# class UploadedFileAdminForm(forms.ModelForm):
#     upload_file = forms.FileField(required=False, help_text="Select a file to upload")

#     class Meta:
#         model = UploadedFile
#         fields = ["file_name", "file_type", "upload_file"]

#     def save(self, commit=True):
#         instance = super().save(commit=False)
#         uploaded_file = self.cleaned_data.get("upload_file")

#         if uploaded_file:
#             if instance.file_type == "video":
#                 file_url = upload_video_to_digital_ocean(uploaded_file)
#             else:
#                 file_url = upload_file_to_digital_ocean(uploaded_file)
            
#             instance.file_url = file_url
#             instance.file_name = uploaded_file.name

#         if commit:
#             instance.save()
#         return instance


# @admin.register(UploadedFile)
# class UploadedFileAdmin(admin.ModelAdmin):
#     form = UploadedFileAdminForm
#     list_display = ("file_name", "file_type", "file_url", "uploaded_at")
#     readonly_fields = ("file_url", "uploaded_at")
#     search_fields = ("file_name", "file_type")
