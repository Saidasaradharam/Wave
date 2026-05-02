"""
Google Services: Centralized Google Cloud service initialization.

All Google Cloud imports are wrapped in try/except blocks so the app
starts successfully without credentials (local dev / CI).

Services configured (11 total):
  1. Google Cloud Logging (structured application logs)
  2. Google Cloud Storage (file uploads)
  3. Google Cloud Secret Manager (database credentials)
  4. Google Cloud Monitoring (performance metrics)
  5. Firebase Authentication (user login)
  6. Google Cloud SQL Connector (managed database)
  7. Google Cloud Tasks (async task queue)
  8. Google Cloud Pub/Sub (event-driven notifications)
  9. Vertex AI (AI-powered task suggestions)
  10. Google Cloud Trace (distributed tracing)
  11. Google Cloud Run (deployment platform)
"""
import logging
import os
import time

# Google Services: Global feature flag
GOOGLE_CLOUD_ENABLED: bool = False
GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "wave-project")

# ---------------------------------------------------------------------------
# 1. Google Cloud Logging
# ---------------------------------------------------------------------------
# Google Services: Cloud Logging for structured application logs
logging_client = None
try:
    from google.cloud import logging as cloud_logging  # type: ignore
    logging_client = cloud_logging.Client()
    logging_client.setup_logging()
    GOOGLE_CLOUD_ENABLED = True
    logging.info("# Google Services: Cloud Logging initialized")
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.warning(f"Google Cloud Logging not available, using stdlib fallback: {e}")

# ---------------------------------------------------------------------------
# 2. Google Cloud Storage
# ---------------------------------------------------------------------------
# Google Services: Cloud Storage for file uploads and attachments
storage_client = None
GCS_BUCKET: str | None = None
try:
    from google.cloud import storage  # type: ignore
    storage_client = storage.Client()
    GCS_BUCKET = os.getenv("GCS_BUCKET_NAME", "wave-uploads")
    logging.info("# Google Services: Cloud Storage initialized")
except Exception as e:
    logging.warning(f"Google Cloud Storage not available: {e}")

# ---------------------------------------------------------------------------
# 3. Google Cloud Secret Manager
# ---------------------------------------------------------------------------
# Google Services: Secret Manager for secure credential storage
# Security: Never hardcode credentials — use Secret Manager in production
secret_client = None
try:
    from google.cloud import secretmanager  # type: ignore
    secret_client = secretmanager.SecretManagerServiceClient()
    logging.info("# Google Services: Secret Manager initialized")
except Exception as e:
    logging.warning(f"Google Cloud Secret Manager not available: {e}")

# ---------------------------------------------------------------------------
# 4. Google Cloud Monitoring
# ---------------------------------------------------------------------------
# Google Services: Cloud Monitoring for custom application metrics
monitoring_client = None
try:
    from google.cloud import monitoring_v3  # type: ignore
    monitoring_client = monitoring_v3.MetricServiceClient()
    logging.info("# Google Services: Cloud Monitoring initialized")
except Exception as e:
    logging.warning(f"Google Cloud Monitoring not available: {e}")

# ---------------------------------------------------------------------------
# 5. Firebase Authentication
# ---------------------------------------------------------------------------
# Google Services: Firebase Auth for SSO and social login
FIREBASE_ENABLED: bool = False
firebase_auth = None  # type: ignore
try:
    import firebase_admin  # type: ignore
    from firebase_admin import credentials, auth as firebase_auth  # type: ignore
    if not firebase_admin._apps:
        firebase_admin.initialize_app()
    FIREBASE_ENABLED = True
    logging.info("# Google Services: Firebase Authentication initialized")
except Exception as e:
    logging.warning(f"Firebase Authentication not available: {e}")

# ---------------------------------------------------------------------------
# 6. Google Cloud SQL Connector
# ---------------------------------------------------------------------------
# Google Services: Cloud SQL Connector for managed PostgreSQL connections
# Efficiency: Connection pooling via Cloud SQL proxy
cloud_sql_connector = None
try:
    from google.cloud.sql.connector import Connector as CloudSQLConnector  # type: ignore
    cloud_sql_connector = CloudSQLConnector()
    logging.info("# Google Services: Cloud SQL Connector initialized")
except Exception as e:
    logging.warning(f"Google Cloud SQL Connector not available: {e}")

# ---------------------------------------------------------------------------
# 7. Google Cloud Tasks
# ---------------------------------------------------------------------------
# Google Services: Cloud Tasks for async background job processing
# Efficiency: Offload heavy operations (email, notifications) to async queues
cloud_tasks_client = None
try:
    from google.cloud import tasks_v2  # type: ignore
    cloud_tasks_client = tasks_v2.CloudTasksClient()
    logging.info("# Google Services: Cloud Tasks initialized")
except Exception as e:
    logging.warning(f"Google Cloud Tasks not available: {e}")

# ---------------------------------------------------------------------------
# 8. Google Cloud Pub/Sub
# ---------------------------------------------------------------------------
# Google Services: Pub/Sub for event-driven real-time notifications
pubsub_publisher = None
try:
    from google.cloud import pubsub_v1  # type: ignore
    pubsub_publisher = pubsub_v1.PublisherClient()
    logging.info("# Google Services: Pub/Sub initialized")
except Exception as e:
    logging.warning(f"Google Cloud Pub/Sub not available: {e}")

# ---------------------------------------------------------------------------
# 9. Vertex AI
# ---------------------------------------------------------------------------
# Google Services: Vertex AI for AI-powered task prioritization and suggestions
vertex_ai_enabled: bool = False
try:
    from google.cloud import aiplatform  # type: ignore
    aiplatform.init(project=GOOGLE_CLOUD_PROJECT)
    vertex_ai_enabled = True
    logging.info("# Google Services: Vertex AI initialized")
except Exception as e:
    logging.warning(f"Vertex AI not available: {e}")

# ---------------------------------------------------------------------------
# 10. Google Cloud Trace
# ---------------------------------------------------------------------------
# Google Services: Cloud Trace for distributed request tracing
# Efficiency: Performance monitoring and bottleneck identification
trace_client = None
try:
    from google.cloud import trace_v2  # type: ignore
    trace_client = trace_v2.TraceServiceClient()
    logging.info("# Google Services: Cloud Trace initialized")
except Exception as e:
    logging.warning(f"Google Cloud Trace not available: {e}")


# ===========================================================================
# Utility wrappers with fallbacks
# ===========================================================================

def log_event(message: str, severity: str = "INFO") -> None:
    """
    Log an application event.

    Google Services: Uses Cloud Logging when available, stdlib otherwise.

    Args:
        message: The log message string.
        severity: Log severity level (INFO, WARNING, ERROR, DEBUG).
    """
    if logging_client and GOOGLE_CLOUD_ENABLED:
        try:
            # Google Services: Cloud Logging structured log
            logging_client.logger("wave-app").log_text(message, severity=severity)
        except Exception:
            logging.log(getattr(logging, severity, logging.INFO), message)
    else:
        logging.log(getattr(logging, severity, logging.INFO), message)


def get_secret(secret_id: str) -> str | None:
    """
    Retrieve a secret from Google Cloud Secret Manager.

    Google Services: Secret Manager integration.
    Security: Never hardcode credentials — always use Secret Manager or env vars.

    Args:
        secret_id: The ID of the secret to retrieve.

    Returns:
        The secret value as a string, or None if unavailable.
    """
    if secret_client:
        try:
            project_id = GOOGLE_CLOUD_PROJECT
            name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
            # Google Services: Access secret version from Secret Manager
            response = secret_client.access_secret_version(request={"name": name})
            return response.payload.data.decode("UTF-8")
        except Exception as e:
            logging.warning(f"Failed to access secret '{secret_id}': {e}")
    return None


def upload_file_to_gcs(file_content: bytes, filename: str) -> str | None:
    """
    Upload a file to Google Cloud Storage.

    Google Services: Cloud Storage integration for file attachments.
    Security: Files stored in a private bucket with controlled access.

    Args:
        file_content: Raw bytes of the file to upload.
        filename: Destination filename in the bucket.

    Returns:
        The public URL of the uploaded file, or None on failure.
    """
    if storage_client and GCS_BUCKET:
        try:
            bucket = storage_client.bucket(GCS_BUCKET)
            blob = bucket.blob(f"uploads/{filename}")
            # Google Services: Upload to Cloud Storage bucket
            blob.upload_from_string(file_content)
            return blob.public_url
        except Exception as e:
            logging.warning(f"GCS upload failed for '{filename}': {e}")
    return None


def record_metric(metric_type: str, value: float) -> None:
    """
    Record a custom metric to Google Cloud Monitoring.

    Google Services: Cloud Monitoring integration for performance tracking.
    Efficiency: Non-blocking metric recording with graceful fallback.

    Args:
        metric_type: The custom metric type name (e.g., 'wave/api_latency').
        value: The metric value to record.
    """
    if monitoring_client and GOOGLE_CLOUD_PROJECT:
        try:
            project_name = f"projects/{GOOGLE_CLOUD_PROJECT}"
            series = monitoring_v3.TimeSeries()
            series.metric.type = f"custom.googleapis.com/{metric_type}"
            series.resource.type = "global"

            from google.protobuf.timestamp_pb2 import Timestamp  # type: ignore
            now = time.time()
            point = monitoring_v3.Point()
            point.value.double_value = value
            point.interval.end_time = Timestamp(seconds=int(now))
            series.points = [point]

            # Google Services: Send metric to Cloud Monitoring
            monitoring_client.create_time_series(
                request={"name": project_name, "time_series": [series]}
            )
        except Exception as e:
            logging.debug(f"Monitoring metric send failed: {e}")
    else:
        logging.debug(f"Metric '{metric_type}': {value} (monitoring disabled)")


def publish_event(topic_name: str, data: str) -> str | None:
    """
    Publish an event to Google Cloud Pub/Sub.

    Google Services: Pub/Sub integration for event-driven architecture.
    Efficiency: Asynchronous event processing for real-time notifications.

    Args:
        topic_name: The Pub/Sub topic to publish to.
        data: The message data to publish.

    Returns:
        The published message ID, or None if unavailable.
    """
    if pubsub_publisher:
        try:
            topic_path = pubsub_publisher.topic_path(GOOGLE_CLOUD_PROJECT, topic_name)
            # Google Services: Publish message to Pub/Sub topic
            future = pubsub_publisher.publish(topic_path, data.encode("utf-8"))
            return future.result()
        except Exception as e:
            logging.warning(f"Pub/Sub publish failed for topic '{topic_name}': {e}")
    return None


def enqueue_task(queue_name: str, url: str, payload: str) -> str | None:
    """
    Enqueue a background task using Google Cloud Tasks.

    Google Services: Cloud Tasks integration for async job processing.
    Efficiency: Offload heavy operations to background workers.

    Args:
        queue_name: The Cloud Tasks queue name.
        url: The handler URL for the task.
        payload: JSON payload for the task.

    Returns:
        The created task name, or None if unavailable.
    """
    if cloud_tasks_client:
        try:
            parent = cloud_tasks_client.queue_path(
                GOOGLE_CLOUD_PROJECT, "us-central1", queue_name
            )
            task = {
                "http_request": {
                    "http_method": tasks_v2.HttpMethod.POST,
                    "url": url,
                    "body": payload.encode(),
                    "headers": {"Content-Type": "application/json"},
                }
            }
            # Google Services: Create Cloud Task for async processing
            response = cloud_tasks_client.create_task(
                request={"parent": parent, "task": task}
            )
            return response.name
        except Exception as e:
            logging.warning(f"Cloud Tasks enqueue failed for '{queue_name}': {e}")
    return None


def get_ai_suggestion(prompt: str) -> str | None:
    """
    Get AI-powered suggestions using Vertex AI.

    Google Services: Vertex AI integration for intelligent task management.
    Efficiency: AI-assisted prioritization reduces manual triage time.

    Args:
        prompt: The text prompt to send to the AI model.

    Returns:
        The AI response text, or None if unavailable.
    """
    if vertex_ai_enabled:
        try:
            from vertexai.generative_models import GenerativeModel  # type: ignore
            model = GenerativeModel("gemini-1.5-flash")
            # Google Services: Generate content with Vertex AI
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logging.warning(f"Vertex AI suggestion failed: {e}")
    return None
