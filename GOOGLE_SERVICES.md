# Google Cloud Services Integration — Wave Platform

## Overview

Wave integrates **11 Google Cloud services** for a production-ready, enterprise-grade team coordination platform. All services are wrapped in `try/except` blocks with graceful fallbacks, allowing the application to run in any environment — from local development to Google Cloud Run.

## Services

### 1. Google Cloud Logging
- **Package:** `google-cloud-logging`
- **Usage:** Structured application logging for all API events (auth, tasks, projects, comments)
- **File:** `google_services.py` → `log_event()`
- **Fallback:** Python `logging` stdlib

### 2. Google Cloud Storage
- **Package:** `google-cloud-storage`
- **Usage:** File uploads and task attachments stored in GCS buckets
- **File:** `google_services.py` → `upload_file_to_gcs()`
- **Fallback:** Local file system storage

### 3. Google Cloud Secret Manager
- **Package:** `google-cloud-secret-manager`
- **Usage:** Secure storage for database credentials, JWT secrets, API keys
- **File:** `google_services.py` → `get_secret()`, `database.py` → `get_database_url()`
- **Fallback:** `.env` environment variables

### 4. Google Cloud Monitoring
- **Package:** `google-cloud-monitoring`
- **Usage:** Custom application metrics (API latency, user activity, error rates)
- **File:** `google_services.py` → `record_metric()`
- **Fallback:** Debug-level log messages

### 5. Firebase Authentication
- **Package:** `firebase-admin`
- **Usage:** SSO and social login integration (Google, GitHub)
- **File:** `google_services.py` → `firebase_auth`, `auth.py` → `get_current_user()`
- **Fallback:** Local JWT authentication with `python-jose`

### 6. Google Cloud SQL Connector
- **Package:** `cloud-sql-python-connector`
- **Usage:** Managed PostgreSQL connection pooling for Cloud SQL instances
- **File:** `google_services.py` → `cloud_sql_connector`
- **Fallback:** Direct PostgreSQL connection via `asyncpg` or SQLite

### 7. Google Cloud Tasks
- **Package:** `google-cloud-tasks`
- **Usage:** Async background job processing (email notifications, report generation)
- **File:** `google_services.py` → `enqueue_task()`
- **Fallback:** Synchronous processing within request lifecycle

### 8. Google Cloud Pub/Sub
- **Package:** `google-cloud-pubsub`
- **Usage:** Event-driven real-time notifications and inter-service communication
- **File:** `google_services.py` → `publish_event()`
- **Fallback:** In-process event handling

### 9. Vertex AI
- **Package:** `google-cloud-aiplatform`
- **Usage:** AI-powered task prioritization, smart suggestions, and content analysis
- **File:** `google_services.py` → `get_ai_suggestion()`
- **Fallback:** Returns `None` (manual prioritization)

### 10. Google Cloud Trace
- **Package:** `google-cloud-trace`
- **Usage:** Distributed request tracing for performance monitoring and bottleneck detection
- **File:** `google_services.py` → `trace_client`
- **Fallback:** No tracing (uses standard request logging)

### 11. Google Cloud Run
- **Platform:** Deployment target
- **Usage:** Serverless container deployment with auto-scaling
- **Files:** `Dockerfile`, `main.py` (static file serving, health check endpoint)
- **Config:** `PORT` environment variable, `uvicorn` ASGI server

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud Run                       │
│  ┌───────────────────────────────────────────────────┐   │
│  │              FastAPI Application                   │   │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────────┐   │   │
│  │  │ Auth    │  │ Projects │  │ Notifications  │   │   │
│  │  │ Routes  │  │ Routes   │  │ Routes         │   │   │
│  │  └────┬────┘  └────┬─────┘  └────────┬───────┘   │   │
│  │       │            │                  │           │   │
│  │  ┌────▼────────────▼──────────────────▼───────┐   │   │
│  │  │         google_services.py                  │   │   │
│  │  │  Cloud Logging | Storage | Secret Manager  │   │   │
│  │  │  Monitoring | Firebase | Cloud SQL         │   │   │
│  │  │  Cloud Tasks | Pub/Sub | Vertex AI | Trace │   │   │
│  │  └────────────────────────────────────────────┘   │   │
│  └───────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `GOOGLE_CLOUD_PROJECT` | GCP Project ID | `wave-project` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Auto-detected |
| `GCS_BUCKET_NAME` | Cloud Storage bucket name | `wave-uploads` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./wave.db` |
| `SECRET_KEY` | JWT signing secret | Dev fallback |

## Graceful Degradation

All Google Cloud services follow this pattern:

```python
# Google Services: [Service Name] initialization
try:
    from google.cloud import [service]
    client = [service].Client()
    SERVICE_ENABLED = True
except Exception:
    SERVICE_ENABLED = False
    # Fallback to local alternative
```

The application is fully functional without any Google Cloud credentials. Services degrade gracefully:
- **Cloud Logging** → Python `logging.info()`
- **Secret Manager** → Environment variables (`.env`)
- **Cloud Storage** → Local file system
- **Firebase Auth** → Local JWT with `python-jose`
- **Cloud SQL** → Local SQLite database
- **Cloud Monitoring** → Debug log messages
- **Vertex AI** → Manual task management (no AI suggestions)
