## **Scalable Image Import System**
The Image Import System is a scalable backend system that import images from a public Google Drive folder and store them in cloud object storage while persisting image metadata in a SQL database. The system exposes APIs to trigger the import process and to retrieve the list of imported images. The system is designed as a scalable, multi-service backend system capable of handling large-scale image imports efficiently.

## **Architecture Overview**
The system is designed using a **multi-service architecture**, where each service is loosely coupled and has a single responsibility. Instead of handling image imports synchronously, the system relies on **asynchronous processing** through **message queues** and **background workers** to ensure scalability and parallelism. This design ensures that heavy operations such as folder scanning and image uploads do not block API requests, and each service can be scaled independently based on load.

High-level workflow of the system:
- A client triggers an import by providing a public Google Drive folder URL.
- A crawler service scans the folder and identifies image files in it.
- Uploader workers, horizontally scallable, runs parallelly and upload all the images to cloud object storage.
- A metadata service persists image metadata into a SQL database.
- API endpoints allows client to trigger import and retrieve requests.

![Architecture Diagram](docs/import%20system%20workflow.jpg)

## **Service Breakdown**
The system is composed of multiple loosely coupled services, each responsible for a specific part of the workflow. This separation allows independent scaling and improves maintainability. The services are as follows:

#### **API Service**
Exposes HTTP endpoints to trigger the image import process and to retrieve imported image metadata. It acts as the entry point for clients while remaining lightweight by offloading heavy work to background services.

#### **Crawler Service**
Consumes folder import requests and scans the provided Google Drive folder for image files. For each image found, it generates a task and pushes it to the file task queue for further processing.

#### **Uploader Service**
Consumes image tasks from the queue and streams image data directly from Google Drive to cloud object storage. This avoids local disk usage and allows multiple uploader workers to run in parallel for high-throughput imports.

#### **Metadata Service**
Processes metadata events generated after successful uploads and persists image metadata (such as name, size, MIME type, and storage path) into the SQL database.

#### **Infrastructure Components**

- **Message Queues**: Used to decouple services and enable asynchronous, event-driven processing.
- **Object Storage**: Stores uploaded images in a scalable and durable manner.
- **SQL Database**: Stores image metadata for querying and retrieval.

## **API Documentation**
#### **POST /import/google-drive**
Triggers the import of images from public Google Drive Folder.
#### Request body:
```json
{
    "folder_url": "https://drive.google.com/drive/folders/<folder_id>"
}
```
#### Response:
```json
{
  "status": "accepted",
  "message": "Folder import started"
}
```
This endpoint returns immediately after validating the request. The actual import process is handled asynchronously by background workers.

#### **GET /images**
#### Response:
```json
[
  {
    "name": "example.jpg",
    "google_drive_id": "1AbCdEfGh",
    "size": 245678,
    "mime_type": "image/jpeg",
    "storage_path": "https://<object-storage-url>/example.jpg"
  }
]
```
This endpoint reads from the metadata database and retrieves metadata.

## **Setup Instructions**
#### **Local Setup**
The system can be run locally using Docker Compose, which starts all required services including the API, background workers, database, message queue, and object storage. You need Docker and Docker Compose installed locally. Also install all the python packages from requirements.txt files. Then follow these steps:
1. Clone the repository.
2. Create environment variables files (.env) using the provided .env.example files.
3. Start all services:
```bash 
docker-compose up --build
```
4. Once the containers are running, access the app using http://localhost:8000.

#### **Cloud Setup**
The same Docker Compose setup can be deployed on a cloud virtual machine.
1. Create a VM on any cloud provider (for example AWS, GCP, Azure etc).
2. Install Docker and Docker Compose on the VM.
3. Clone the repository.
4. Configure environment variables.
5. Start the containers.

## **Notes on Scalability and Large-Scale Imports**
The system is designed to handle large-scale image imports (for example thousands of images) by relying on asynchronous, event-driven processing rather than synchronous API execution.

**Queue-based processing:** Message queues act as buffers between services, allowing the system to absorb spikes in load without overwhelming any single component.

**Horizontal scaling of workers:** Crawler, uploader, and metadata workers can be scaled independently by running multiple instances, enabling parallel processing of image tasks.

**Streaming uploads:** Images are streamed directly from Google Drive to object storage, avoiding local disk usage and reducing memory overhead.

**Loose coupling and fault tolerance:** Services are decoupled through queues, allowing individual components to restart or scale without impacting the entire system.

This design ensures the system remains performant, resilient, and cloud-ready even as the number of imported images grows significantly.