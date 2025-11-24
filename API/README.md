# CV Automation REST API Documentation

## Overview

The CV Automation REST API provides programmatic access to the CV processing system. All endpoints require API key authentication.

**Base URL:** `http://localhost:8000/api`

**Interactive Documentation:** `http://localhost:8000/api/docs` (Swagger UI)

---

## Authentication

All endpoints require an API key in the `X-API-Key` header.

### Generate API Key

```bash
python scripts/create_api_key.py --name "My Application"
```

### Using API Key

```bash
curl -H "X-API-Key: YOUR_API_KEY_HERE" http://localhost:8000/api/health
```

---

## Endpoints

### 1. Health Check

Check API and component status.

**Endpoint:** `GET /api/health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-10-20T10:00:00",
  "version": "0.2.0",
  "components": {
    "database": "ok",
    "extractor": "ok",
    "parser": "ok",
    "generator": "ok"
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/health
```

---

### 2. Upload Single CV

Upload and process a single CV file.

**Endpoint:** `POST /api/upload`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Parameters:**
- `file` (required): CV file (PDF, DOCX, or DOC)

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "completed",
  "message": "CV processed successfully",
  "result": {
    "person_name": "John Doe",
    "confidence_score": 0.92,
    "download_url": "/api/download/abc123..."
  }
}
```

**Example:**
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@cv_john_doe.pdf" \
  http://localhost:8000/api/upload
```

---

### 3. Check Status

Check the status of a processing job.

**Endpoint:** `GET /api/status/{job_id}`

**Authentication:** Required

**Path Parameters:**
- `job_id`: Job identifier from upload response

**Response:**
```json
{
  "job_id": "abc123...",
  "status": "completed",
  "file_name": "cv_john_doe.pdf",
  "progress": 100,
  "confidence_score": 0.92,
  "strategy_used": "hybrid",
  "needs_review": false,
  "result": {
    "output_file": "/path/to/output.docx",
    "download_url": "/api/download/abc123...",
    "confidence_score": 0.92,
    "processing_time": 12.5
  }
}
```

**Example:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/status/abc123...
```

---

### 4. Get Results

Get detailed results for a processed CV.

**Endpoint:** `GET /api/results/{cv_id}`

**Authentication:** Required

**Path Parameters:**
- `cv_id`: CV identifier

**Response:**
```json
{
  "cv_id": "abc123...",
  "file_name": "cv_john_doe.pdf",
  "status": "completed",
  "confidence_score": 0.92,
  "processing_time": 12.5,
  "download_url": "/api/download/abc123...",
  "output_file": "/path/to/output.docx",
  "validation_issues": [],
  "processed_date": "2025-10-20T10:00:00"
}
```

**Example:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/results/abc123...
```

---

### 5. Download Resumé

Download the generated Resumé file.

**Endpoint:** `GET /api/download/{cv_id}`

**Authentication:** Required

**Path Parameters:**
- `cv_id`: CV identifier

**Response:** DOCX file

**Example:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/download/abc123... \
  -o resume.docx
```

---

### 6. Upload Batch

Upload multiple CVs for batch processing.

**Endpoint:** `POST /api/batch`

**Authentication:** Required

**Content-Type:** `multipart/form-data`

**Parameters:**
- `files` (required): Multiple CV files

**Response:**
```json
{
  "batch_id": "batch123...",
  "total_files": 10,
  "status": "queued",
  "message": "Batch of 10 files queued for processing",
  "status_url": "/api/batch/batch123.../status",
  "file_ids": ["id1", "id2", ...]
}
```

**Example:**
```bash
curl -X POST \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "files=@cv1.pdf" \
  -F "files=@cv2.pdf" \
  -F "files=@cv3.pdf" \
  http://localhost:8000/api/batch
```

---

### 7. Check Batch Status

Check the status of a batch processing job.

**Endpoint:** `GET /api/batch/{batch_id}/status`

**Authentication:** Required

**Path Parameters:**
- `batch_id`: Batch identifier

**Response:**
```json
{
  "batch_id": "batch123...",
  "status": "processing",
  "total_files": 10,
  "processed_files": 7,
  "successful_files": 6,
  "failed_files": 1,
  "progress": 70.0,
  "current_file": "cv8.pdf",
  "average_confidence": 0.89,
  "eta_seconds": 45,
  "started_at": "2025-10-20T10:00:00",
  "completed_at": null
}
```

**Example:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/batch/batch123.../status
```

---

### 8. Get Batch Results

Get results for all files in a batch.

**Endpoint:** `GET /api/batch/{batch_id}/results`

**Authentication:** Required

**Path Parameters:**
- `batch_id`: Batch identifier

**Response:**
```json
{
  "batch_id": "batch123...",
  "status": "completed",
  "total_files": 10,
  "successful_files": 9,
  "failed_files": 1,
  "average_confidence": 0.91,
  "message": "Batch processing results available"
}
```

**Example:**
```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/api/batch/batch123.../results
```

---

## Rate Limits

Default rate limits per API key:
- **100 requests per minute**
- **1000 CVs per day**

Rate limits can be customized when creating API keys:
```bash
python scripts/create_api_key.py \
  --name "High Volume App" \
  --rate-limit 500 \
  --daily-limit 10000
```

---

## Error Responses

All endpoints return standard error responses:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common HTTP Status Codes:**
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Best Practices

### 1. Handle Asynchronous Processing

CV processing may take time. Use the status endpoint to poll for completion:

```python
import time
import requests

# Upload CV
response = requests.post(
    "http://localhost:8000/api/upload",
    headers={"X-API-Key": API_KEY},
    files={"file": open("cv.pdf", "rb")}
)
job_id = response.json()["job_id"]

# Poll status
while True:
    status = requests.get(
        f"http://localhost:8000/api/status/{job_id}",
        headers={"X-API-Key": API_KEY}
    ).json()
    
    if status["status"] in ["completed", "failed"]:
        break
    
    time.sleep(2)  # Wait 2 seconds between polls
```

### 2. Batch Processing for Multiple CVs

Use the batch endpoint for better efficiency:

```python
files = [
    ("files", open("cv1.pdf", "rb")),
    ("files", open("cv2.pdf", "rb")),
    ("files", open("cv3.pdf", "rb"))
]

response = requests.post(
    "http://localhost:8000/api/batch",
    headers={"X-API-Key": API_KEY},
    files=files
)
```

### 3. Error Handling

Always check for errors and handle them gracefully:

```python
try:
    response = requests.post(...)
    response.raise_for_status()
    data = response.json()
except requests.exceptions.HTTPError as e:
    print(f"API Error: {e.response.json()['detail']}")
except Exception as e:
    print(f"Error: {e}")
```

---

## Python SDK Example

```python
import requests

class CVAutomationClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def upload_cv(self, file_path):
        """Upload and process a CV"""
        with open(file_path, 'rb') as f:
            response = requests.post(
                f"{self.base_url}/upload",
                headers=self.headers,
                files={"file": f}
            )
        response.raise_for_status()
        return response.json()
    
    def get_status(self, job_id):
        """Check processing status"""
        response = requests.get(
            f"{self.base_url}/status/{job_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def download_resume(self, cv_id, output_path):
        """Download generated Resumé"""
        response = requests.get(
            f"{self.base_url}/download/{cv_id}",
            headers=self.headers
        )
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)

# Usage
client = CVAutomationClient(
    base_url="http://localhost:8000/api",
    api_key="YOUR_API_KEY"
)

result = client.upload_cv("cv.pdf")
print(f"Job ID: {result['job_id']}")
```

---

## Support

For API issues or questions:
- Check interactive docs: http://localhost:8000/api/docs
- Review logs: `docker-compose logs -f`
- Check health endpoint: http://localhost:8000/api/health

---

**Last Updated:** October 20, 2025  
**Version:** 0.2.0

