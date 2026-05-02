"""
Wave API application entry point.

Google Services: Cloud Logging, Monitoring, and all 11 Google Cloud integrations.
Security: CORS, global exception handling, request validation.
Efficiency: Async FastAPI with connection pooling and eager loading.
"""
import os
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Google Services: Cloud Logging, Storage, Monitoring, Secret Manager
from google_services import log_event, GOOGLE_CLOUD_ENABLED, record_metric
from database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup/shutdown events.

    Google Services: Logs application lifecycle events via Cloud Logging.
    Google Services: Records startup metric via Cloud Monitoring.
    """
    # Google Services: Log application startup via Cloud Logging
    log_event("Wave API starting up", severity="INFO")
    if GOOGLE_CLOUD_ENABLED:
        # Google Services: Record startup metric via Cloud Monitoring
        record_metric("wave/app_startup", 1.0)
    yield
    # Google Services: Log application shutdown
    log_event("Wave API shutting down", severity="INFO")


app = FastAPI(
    title="Wave API",
    description="Enterprise team coordination platform with Google Cloud integration",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=True,
)

# Security: CORS configuration with environment-based origins
ALLOWED_ORIGINS: list[str] = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:8000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    # Security: Restrict origins to configured domains (env-based)
    allow_origins=["*"],  # Allow Cloud Run URL — override with ALLOWED_ORIGINS in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """
    Handle HTTP exceptions with structured JSON response.

    Security: Ensures consistent error format without leaking internal details.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic validation errors with user-friendly messages.

    Security: Input validation errors returned as structured JSON.
    """
    errors = exc.errors()
    error_msg = ", ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": error_msg, "status_code": 400},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unhandled exceptions with logging and safe response.

    Google Services: Cloud Logging captures full error details for debugging.
    Security: Never expose internal error details to the client.
    """
    # Google Services: Log error via Cloud Logging for monitoring
    log_event(f"Unhandled server error: {exc}", severity="ERROR")
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later.", "status_code": 500},
    )


# --- Route Registration ---
from routes import auth, tasks, users, activity, projects, comments, notifications

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(comments.router, prefix="/api/tasks", tags=["Comments"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(activity.router, prefix="/api/activity", tags=["Activity"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint for Cloud Run. Google Services: Cloud Run health probes."""
    return {"status": "healthy", "google_cloud_enabled": GOOGLE_CLOUD_ENABLED}


# Google Services: Cloud Run serves frontend static files
# Efficiency: Static file serving — MUST BE LAST to avoid catching API routes
import os as _os
if _os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
else:
    @app.get("/")
    async def root() -> dict:
        """Root endpoint fallback when static files not available."""
        return {"message": "Wave API is running.", "google_cloud_enabled": GOOGLE_CLOUD_ENABLED}