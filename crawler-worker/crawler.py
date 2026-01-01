from googleapiclient.discovery import build
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DRIVE_API_KEY")
FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
QUEUE_NAME = "file_tasks"
IMAGE_MIME_PREFIX = "image/"


def list_and_enqueue_images():
    service = build(
        "drive",
        "v3",
        developerKey=API_KEY
    )

    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    query = f"'{FOLDER_ID}' in parents and trashed = false"

    page_token = None
    pushed = 0

    while True:
        results = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageSize=100,
            pageToken=page_token
        ).execute()

        files = results.get("files", [])

        for file in files:
            mime_type = file.get("mimeType", "")

            if not mime_type.startswith(IMAGE_MIME_PREFIX):
                continue

            task = {
                "file_id": file.get("id"),
                "name": file.get("name"),
                "mime_type": mime_type,
                "size": int(file.get("size", 0))
            }

            r.rpush(QUEUE_NAME, json.dumps(task))
            pushed += 1

        page_token = results.get("nextPageToken")
        if not page_token:
            break

    print(f"Pushed {pushed} image tasks to Redis queue '{QUEUE_NAME}'")


if __name__ == "__main__":
    list_and_enqueue_images()
