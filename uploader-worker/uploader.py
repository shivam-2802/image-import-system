import os
from dotenv import load_dotenv
import boto3
from botocore.client import Config
import redis

load_dotenv()

# MinIO Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
QUEUE_NAME = "file_tasks"

# Test Image
IMAGE_PATH = "test_images/sample.jpg"
OBJECT_NAME = "sample.jpg"


def upload_to_minio():
    s3_client = boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )

    s3_client.upload_file(
        IMAGE_PATH,
        MINIO_BUCKET,
        OBJECT_NAME
    )

    print("Uploaded image to MinIO")


def connect_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )


if __name__ == "__main__":
    upload_to_minio()
