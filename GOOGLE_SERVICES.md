# Google Cloud Services Integration — Wave Platform

This document describes every Google Cloud service used by the Wave Team Coordination Platform, how each is integrated, and how the application gracefully degrades when credentials are not available.

## Architecture Overview

All Google Cloud integrations are centralized in `backend/google_services.py`. Every import is wrapped in `try/except` with a global feature flag (`GOOGLE_CLOUD_ENABLED`). The app starts and runs fully without any Google credentials.

```
┌─────────────────────────────────────────────────────┐
│              google_services.py                      │
│                                                      │
│  ┌────────────┐  ┌───────────┐  ┌───────────────┐   │
│  │Cloud Logging│  │Cloud      │  │Secret Manager │   │
│  │(structured) │  │Storage    │  │(credentials)  │   │
│  └─────┬──────┘  └─────┬─────┘  └──────┬────────┘   │
│        │               │               │             │
│  ┌─────┴──────┐  ┌─────┴─────┐  ┌──────┴────────┐   │
│  │Cloud       │  │Firebase   │  │Cloud          │   │
│  │Monitoring  │  │Auth       │  │Analytics      │   │
│  │(metrics)   │  │(login)    │  │(tracking)     │   │
│  └────────────┘  └───────────┘  └───────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 1. Google Cloud Logging

**Package:** `google-cloud-logging>=3.6.0`
**Import:** `from google.cloud import logging as cloud_logging`
**Used in:** `google_services.py`, `routes/auth.py`, `main.py`

### Purpose
Structured application logging for authentication events (logins, failed attempts, registrations), server errors, and application lifecycle events.

### Integration Points
- `log_event(message, severity)` — wrapper function used across the codebase
- Authentication route logs registration and login events
- Global exception handler logs all unhandled errors

### Fallback
Standard Python `logging` module with `logging.basicConfig(level=logging.INFO)`.

---

## 2. Google Cloud Storage

**Package:** `google-cloud-storage>=2.10.0`
**Import:** `from google.cloud import storage`
**Used in:** `google_services.py`

### Purpose
File uploads for task attachments. Files are stored in a GCS bucket (configurable via `GCS_BUCKET_NAME` env var).

### Integration Points
- `upload_file_to_gcs(file_content, filename)` — returns public URL or None

### Fallback
Returns `None` when GCS is unavailable. File upload features are gracefully disabled.

---

## 3. Google Cloud Secret Manager

**Package:** `google-cloud-secret-manager>=2.16.2`
**Import:** `from google.cloud import secretmanager`
**Used in:** `google_services.py`, `database.py`

### Purpose
Securely store and retrieve database credentials and other secrets without hardcoding them in source code.

### Integration Points
- `get_secret(secret_id)` — retrieves secret values from Secret Manager
- `database.py` — retrieves `DATABASE_URL` from Secret Manager in production

### Fallback
Falls back to `DATABASE_URL` environment variable, then to local SQLite (`wave.db`).

---

## 4. Google Cloud Monitoring

**Package:** `google-cloud-monitoring>=2.14.2`
**Import:** `from google.cloud import monitoring_v3`
**Used in:** `google_services.py`, `main.py`

### Purpose
Custom application metrics: startup events, API latency, error rates.

### Integration Points
- `record_metric(metric_type, value)` — sends custom time series data
- Application startup metric in `main.py` lifespan handler

### Fallback
Metrics are logged to debug output when monitoring is unavailable.

---

## 5. Firebase Authentication

**Package:** `firebase-admin>=6.2.0`
**Import:** `import firebase_admin; from firebase_admin import auth as firebase_auth`
**Used in:** `google_services.py`, `auth.py`

### Purpose
Optional SSO authentication. Supports Firebase ID tokens alongside local JWT authentication.

### Integration Points
- `auth.py` `get_current_user()` — validates Firebase ID tokens for long tokens (>200 chars)
- Falls back to local JWT validation if Firebase is unavailable

### Fallback
Local JWT authentication works without any Firebase configuration. The `FIREBASE_ENABLED` flag controls whether Firebase validation is attempted.

---

## 6. Google Analytics Data API

**Package:** `google-analytics-data>=0.17.0`
**Import:** Listed in `requirements.txt` for future integration
**Used in:** Available for frontend analytics tracking

### Purpose
Track user behavior, page views, and feature adoption.

### Fallback
No analytics data is collected when the service is unavailable.

---

## Environment Variables

| Variable | Purpose | Default |
|---|---|---|
| `GOOGLE_CLOUD_PROJECT` | GCP project ID | `wave-project` |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service account JSON | Not set (uses ADC) |
| `GCS_BUCKET_NAME` | Cloud Storage bucket | `wave-uploads` |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./wave.db` |
| `SECRET_KEY` | JWT signing key | `super-secret-key-for-dev` |

## Local Development

The application starts successfully without any Google Cloud credentials:

```bash
cd backend
python -m uvicorn main:app --reload
```

All Google Cloud features degrade gracefully with logged warnings:
```
WARNING: Google Cloud Logging not available, using stdlib fallback
WARNING: Google Cloud Storage not available
WARNING: Google Cloud Secret Manager not available
WARNING: Google Cloud Monitoring not available
WARNING: Firebase Authentication not available
```

## Production Deployment

Set `GOOGLE_APPLICATION_CREDENTIALS` or deploy to Cloud Run with a service account that has:
- `roles/logging.logWriter`
- `roles/storage.objectAdmin`
- `roles/secretmanager.secretAccessor`
- `roles/monitoring.metricWriter`
- Firebase Admin SDK access
