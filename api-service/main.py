import os
import json
import redis
import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
FOLDER_QUEUE = "folder_tasks"

# Postgres Config
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# MinIO
MINIO_PUBLIC_ENDPOINT = os.getenv("MINIO_PUBLIC_ENDPOINT")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")

# Clients
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True
)

db_conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

# App
app = FastAPI(title="Image Import API")

# Schemas
class ImportRequest(BaseModel):
    folder_url: str

#Extract Google Drive folder ID from URL
def extract_folder_id(folder_url: str) -> str:
    if "folders/" not in folder_url:
        raise ValueError("Invalid Google Drive folder URL")
    return folder_url.split("folders/")[1].split("?")[0]



# Routes
@app.post("/import/google-drive")
def import_google_drive(request: ImportRequest):
    try:
        folder_id = extract_folder_id(request.folder_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    task = {
        "folder_id": folder_id
    }

    redis_client.rpush(FOLDER_QUEUE, json.dumps(task))

    return {
        "status": "accepted",
        "message": "Folder import started"
    }

@app.get("/images")
def get_images():
    cursor = db_conn.cursor()
    cursor.execute(
        """
        SELECT name, mime_type, size, storage_path
        FROM images
        """
    )

    rows = cursor.fetchall()
    cursor.close()

    images = []

    for name, mime_type, size, storage_path in rows:
        # storage_path: s3://bucket/key
        _, path = storage_path.split("s3://")
        bucket, key = path.split("/", 1)

        url = f"{MINIO_PUBLIC_ENDPOINT}/{bucket}/{key}"

        images.append({
            "name": name,
            "mime_type": mime_type,
            "size": size,
            "url": url
        })

    return images
