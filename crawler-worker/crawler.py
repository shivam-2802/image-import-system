from googleapiclient.discovery import build
import redis
import json
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("DRIVE_API_KEY")

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
FOLDER_QUEUE = "folder_tasks"
FILE_QUEUE = "file_tasks"
IMAGE_MIME_PREFIX = "image/"


def crawler_loop():
    service = build(
        "drive",
        "v3",
        developerKey=API_KEY
    )

    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

    print("Crawler worker started. Waiting for folder tasks...")

    while True:
        result = r.blpop(FOLDER_QUEUE, timeout=25)

        if result is None:
            print("No folder tasks. Exiting crawler.")
            break

        _, task_json = result
        task = json.loads(task_json)

        folder_id = task.get("folder_id")
        if not folder_id:
            continue

        print(f"Scanning folder {folder_id}")

        query = f"'{folder_id}' in parents and trashed = false"

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

                r.rpush(FILE_QUEUE, json.dumps(task))
                pushed += 1

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        print(f"Pushed {pushed} image tasks to Redis queue '{FILE_QUEUE}'")


if __name__ == "__main__":
    crawler_loop()
