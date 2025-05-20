import boto3
import os
import time
import random
import re
from rest_framework.exceptions import ValidationError
from django.conf import settings
from boto3.s3.transfer import TransferConfig

AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
AWS_S3_ENDPOINT_URL = settings.AWS_S3_ENDPOINT_URL

s3_client = boto3.client(
    "s3",
    endpoint_url=AWS_S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def generate_unique_filename(original_filename):
    """Generates a unique filename using timestamp and random numbers."""
    file_name, file_extension = os.path.splitext(original_filename)


    file_name = re.sub(r'[^a-zA-Z0-9_-]', '', file_name.replace(" ", "-"))
    
    unique_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
    return f"{file_name}_{unique_id}{file_extension}"


def upload_file_to_digital_ocean(file, folder="uploads"):
    """Uploads a file (any type) to DigitalOcean Spaces and returns the public URL."""
    content_type = file.content_type  
    try:
        file_name = generate_unique_filename(file.name)
        s3_path = f"{folder}/{file_name}"

        config = TransferConfig(
            multipart_threshold=100 * 1024 * 1024,  
            max_concurrency=10,  
            multipart_chunksize=500 * 1024 * 1024,  
            use_threads=True
        )

        s3_client.upload_fileobj(
            file,
            AWS_STORAGE_BUCKET_NAME,
            s3_path,
            ExtraArgs={"ACL": "public-read", "ContentType": content_type},
            Config=config
        )

        public_url = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{s3_path}"
        return  public_url

    except Exception as e:
        raise ValidationError(f"Failed to upload file: {str(e)}")


def upload_video_to_digital_ocean(file):
    """Uploads a large video file using multipart upload to DigitalOcean Spaces."""
    try:
        
        file_name = generate_unique_filename(file.name)
        s3_path = f"tristan_howell/videos/{file_name}"

        config = TransferConfig(
            multipart_threshold=5 * 1024 * 1024 * 1024,  
            max_concurrency=10,  
            multipart_chunksize=1 * 1024 * 1024 * 1024,  
            use_threads=True
        )

        s3_client.upload_fileobj(
            file,
            AWS_STORAGE_BUCKET_NAME,
            s3_path,
            ExtraArgs={"ACL": "public-read", "ContentType": "video/mp4"},
            Config=config
        )

        public_url = f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{s3_path}"
        print(f' Video uploaded successfully: {public_url}')
        return public_url

    except Exception as e:
        raise ValidationError(f"Failed to upload video to DigitalOcean Spaces: {str(e)}")

def delete_file_from_s3(file_url):
    """Deletes a file from DigitalOcean Spaces (S3 bucket) given its public URL."""
    try:

        file_path = file_url.split(f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/")[-1]
        
        s3_client.delete_object(Bucket=AWS_STORAGE_BUCKET_NAME, Key=file_path)
        print(f"✅ File deleted successfully: {file_url}")
    except Exception as e:
        raise ValidationError(f"Failed to delete file from S3: {str(e)}")