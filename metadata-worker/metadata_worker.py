import os
import json
import redis
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Redis Config
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
METADATA_QUEUE = "metadata_tasks"

# Postgres Config
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Clients
def get_redis():
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True
    )

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )



def metadata_worker_loop():
    redis_client = get_redis()
    conn = get_db_connection()
    cursor = conn.cursor()

    print("Metadata worker started. Waiting for tasks...")

    while True:
        _, task_json = redis_client.blpop(METADATA_QUEUE)
        task = json.loads(task_json)

        print(f"Saving metadata for {task['name']}")

        cursor.execute(
            """
            INSERT INTO images (name, google_drive_id, size, mime_type, storage_path)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                task["name"],
                task["google_drive_id"],
                task["size"],
                task["mime_type"],
                task["storage_path"],
            )
        )

        conn.commit()
        print(f"Metadata saved for {task['name']}")

    cursor.close()
    conn.close()



if __name__ == "__main__":
    metadata_worker_loop()
