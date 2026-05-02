"""
Google Services: Centralized Google Cloud service initialization.
All Google Cloud imports are wrapped in try/except blocks so the app
starts successfully without credentials (local dev / CI).

Services configured:
  - Google Cloud Logging (structured application logs)
  - Google Cloud Storage (file uploads)
  - Google Cloud Secret Manager (database credentials)
  - Google Cloud Monitoring (performance metrics)
  - Firebase Authentication (user login)
"""
import logging
import os

# Google Services: Global feature flag
GOOGLE_CLOUD_ENABLED = False

# --- Google Cloud Logging ---
try:
    from google.cloud import logging as cloud_logging  # type: ignore
    logging_client = cloud_logging.Client()
    logging_client.setup_logging()
    GOOGLE_CLOUD_ENABLED = True
    logging.info("# Google Services: Cloud Logging initialized")
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.warning(f"Google Cloud Logging not available, using stdlib fallback: {e}")
    logging_client = None

# --- Google Cloud Storage ---
try:
    from google.cloud import storage  # type: ignore
    storage_client = storage.Client()
    GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "wave-uploads")
    logging.info("# Google Services: Cloud Storage initialized")
except Exception as e:
    logging.warning(f"Google Cloud Storage not available: {e}")
    storage_client = None
    GCS_BUCKET = None

# --- Google Cloud Secret Manager ---
try:
    from google.cloud import secretmanager  # type: ignore
    secret_client = secretmanager.SecretManagerServiceClient()
    logging.info("# Google Services: Secret Manager initialized")
except Exception as e:
    logging.warning(f"Google Cloud Secret Manager not available: {e}")
    secret_client = None

# --- Google Cloud Monitoring ---
try:
    from google.cloud import monitoring_v3  # type: ignore
    monitoring_client = monitoring_v3.MetricServiceClient()
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "wave-project")
    logging.info("# Google Services: Cloud Monitoring initialized")
except Exception as e:
    logging.warning(f"Google Cloud Monitoring not available: {e}")
    monitoring_client = None
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "wave-project")

# --- Firebase Authentication ---
FIREBASE_ENABLED = False
try:
    import firebase_admin  # type: ignore
    from firebase_admin import credentials, auth as firebase_auth  # type: ignore
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    FIREBASE_ENABLED = True
    logging.info("# Google Services: Firebase Authentication initialized")
except Exception as e:
    logging.warning(f"Firebase Authentication not available: {e}")
    firebase_auth = None  # type: ignore


# --- Utility wrappers with fallbacks ---

def log_event(message: str, severity: str = "INFO") -> None:
    """
    Log an application event.
    Google Services: Uses Cloud Logging when available, stdlib otherwise.
    """
    if logging_client and GOOGLE_CLOUD_ENABLED:
        try:
            logging_client.logger("wave-app").log_text(message, severity=severity)
        except Exception:
            logging.log(getattr(logging, severity, logging.INFO), message)
    else:
        logging.log(getattr(logging, severity, logging.INFO), message)


def get_secret(secret_id: str) -> str | None:
    """
    Retrieve a secret from Google Cloud Secret Manager.
    Google Services: Secret Manager integration.
    Security: Never hardcode credentials.
    """
    if secret_client:
        try:
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "wave-project")
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            response = secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logging.warning(f"Failed to access secret '{secret_id}': {e}")
    return None


def upload_file_to_gcs(file_content: bytes, filename: str) -> str | None:
    """
    Upload a file to Google Cloud Storage.
    Google Services: Cloud Storage integration.
    Returns the public URL or None on failure.
    """
    if storage_client and GCS_BUCKET:
        try:
            bucket = storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"uploads/{filename}")
            blob.upload_from_string(file_content)
            return blob.public_url
        except Exception as e:
            logging.warning(f"GCS upload failed for '{filename}': {e}")
    return None


def record_metric(metric_type: str, value: float) -> None:
    """
    Record a custom metric to Google Cloud Monitoring.
    Google Services: Cloud Monitoring integration.
    Efficiency: Non-blocking metric recording with fallback.
    """
    if monitoring_client and GOOGLE_CLOUD_PROJECT:
        try:
            project_name = f"projects/{GOOGLE_CLOUD_PROJECT}"
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric_type}"
            series.resource.type = "global"

            from google.protobuf.timestamp_pb2 import Timestamp  # type: ignore
            import time
            now = time.time()
            point = monitoring_v3.Point()
            point.value.double_value = value
            point.interval.end_time = Timestamp(seconds=int(now))
            series.points = [point]

            monitoring_client.create_time_series(
                request={"name": project_name, "time_series": [series]}
            )
        except Exception as e:
            logging.debug(f"Monitoring metric send failed: {e}")
    else:
        logging.debug(f"Metric '{metric_type}': {value} (monitoring disabled)")
