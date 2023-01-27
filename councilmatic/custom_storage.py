from storages.backends.s3boto3 import S3Boto3Storage
from django.conf import settings


print("from custom_storage:", settings.BUCKET_NAME)


class MediaStorage(S3Boto3Storage):
    bucket_name = settings.BUCKET_NAME
