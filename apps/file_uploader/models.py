from django.db import models

class UploadedFile(models.Model):
    FILE_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
        ("document", "Document"),
        ("other", "Other"),
    ]

    file_name = models.CharField(max_length=255)
    file_url = models.URLField(max_length=500)
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, default="other")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file_name
