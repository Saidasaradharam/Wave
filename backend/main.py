import os
import logging
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

# Google Services: Cloud Logging, Storage, Monitoring, Secret Manager
from google_services import log_event, GOOGLE_CLOUD_ENABLED, record_metric
from database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Google Services: Log application startup
    log_event("Wave API starting up", severity="INFO")
    if GOOGLE_CLOUD_ENABLED:
        record_metric("wave/app_startup", 1.0)
    yield
    log_event("Wave API shutting down", severity="INFO")

app = FastAPI(title="Wave API", lifespan=lifespan)

# Security: CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    errors = exc.errors()
    error_msg = ", ".join([f"{err['loc'][-1]}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": error_msg, "status_code": 400},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions. Google Services: Cloud Logging."""
    log_event(f"Unhandled server error: {exc}", severity="ERROR")
    traceback.print_exc()
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error. Please try again later.", "status_code": 500},
    )

from routes import auth, tasks, users, activity, projects, comments, notifications

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(comments.router, prefix="/api/tasks", tags=["Comments"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(activity.router, prefix="/api/activity", tags=["Activity"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "Wave API is running.", "google_cloud_enabled": GOOGLE_CLOUD_ENABLED}
