import boto3  # type: ignore
from botocore.config import Config  # type: ignore
from django.conf import settings


def aws_creds():
    if settings.AWS_ACCESS_KEY_ID:
        return {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_DEFAULT_REGION,
        }
    else:
        return {
            "region_name": settings.AWS_DEFAULT_REGION,
        }


s3_client = boto3.client("s3", **aws_creds())
ec2_client = boto3.client("ec2", **aws_creds())
