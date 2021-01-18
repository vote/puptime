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


def get_proxy_ec2_client(region):
    if not settings.AWS_PROXY_ROLE_ARN:
        return boto3.client(
            "ec2",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=region,
        )

    sts_client = boto3.client("sts")
    response = sts_client.assume_role(
        RoleArn=settings.AWS_PROXY_ROLE_ARN,
        RoleSessionName=f"puptime-{settings.PROXY_TAG}",
        DurationSeconds=3600,
    )
    assert response.get("ResponseMetadata", {}).get("HTTPStatusCode") == 200
    return boto3.client(
        "ec2",
        aws_access_key_id=response["Credentials"]["AccessKeyId"],
        aws_secret_access_key=response["Credentials"]["SecretAccessKey"],
        aws_session_token=response["Credentials"]["SessionToken"],
        region_name=region,
    )
