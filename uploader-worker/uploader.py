import os
from dotenv import load_dotenv
import boto3
from botocore.client import Config
import redis
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

load_dotenv()

# Google Drive API Key
DRIVE_API_KEY = os.getenv("DRIVE_API_KEY")

# MinIO Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
FILE_TASKS_QUEUE = "file_tasks"
METADATA_QUEUE = "metadata_tasks"


# Clients
def get_drive_service():
    return build("drive", "v3", developerKey=DRIVE_API_KEY)

def get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

def get_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )



# Stream a Google Drive file into MinIO
def stream_drive_file_to_minio(drive_service, s3_client, file_id, object_name):

    request = drive_service.files().get_media(fileId=file_id)

    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    # Rewind stream before upload
    file_stream.seek(0)

    s3_client.upload_fileobj(
        Fileobj=file_stream,
        Bucket=MINIO_BUCKET,
        Key=object_name
    )

def uploader_loop():
    drive_service = get_drive_service()
    redis_client = get_redis()
    s3_client = get_s3_client()

    print("Uploader worker started. Waiting for tasks...")

    while True:
        # Blocking pop
        result = redis_client.blpop(FILE_TASKS_QUEUE, timeout=25)

        if result is None:
            print("No more tasks. Shutting down uploader.")
            break

        _, task_json = result

        task = json.loads(task_json)

        file_id = task["file_id"]
        name = task["name"]
        mime_type = task["mime_type"]
        size = task["size"]

        print(f"Processing {name}")

        # Stream upload
        stream_drive_file_to_minio(
            drive_service=drive_service,
            s3_client=s3_client,
            file_id=file_id,
            object_name=name
        )

        # Build metadata message
        metadata = {
            "name": name,
            "mime_type": mime_type,
            "size": size,
            "storage_path": f"s3://{MINIO_BUCKET}/{name}",
            "google_drive_id": file_id
        }

        redis_client.rpush(METADATA_QUEUE, json.dumps(metadata))

        print(f"Uploaded {name} and queued metadata")



if __name__ == "__main__":
    uploader_loop()