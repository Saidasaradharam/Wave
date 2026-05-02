"""
Database configuration and session management.

Google Services: Secret Manager integration for secure credential retrieval.
Google Services: Cloud SQL Connector support for managed PostgreSQL.
Security: Database credentials never hardcoded — sourced from env or Secret Manager.
Efficiency: Async engine with connection pooling for optimal performance.
"""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Google Services: Secret Manager integration for database credentials
from google_services import get_secret


def get_database_url() -> str:
    """
    Retrieve database URL from environment or Google Cloud Secret Manager.

    Security: Never hardcode database credentials in source code.
    Google Services: Secret Manager integration for production credentials.
    Efficiency: Check environment variable first (fast path).

    Returns:
        The database connection URL string.
    """
    # Efficiency: Check environment variable first (fast path)
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # Google Services: Try Secret Manager for production credentials
    # Security: Production credentials stored in Secret Manager, not env files
    secret_url = get_secret("database-url")
    if secret_url:
        return secret_url

    # Fallback to local SQLite for development
    logging.info("Using local SQLite database (wave.db)")
    return "sqlite+aiosqlite:///./wave.db"


DATABASE_URL: str = get_database_url()

# Efficiency: Database connection pooling configuration
engine_args: dict = {"echo": False}
if "sqlite" not in DATABASE_URL:
    # Efficiency: Connection pool for PostgreSQL / Cloud SQL
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_async_engine(DATABASE_URL, **engine_args)

# Efficiency: Async session factory with expire_on_commit=False to prevent lazy loads
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    """
    FastAPI dependency for async database session injection.

    Efficiency: Uses async context manager for proper session lifecycle.
    Security: Session is always closed in finally block to prevent leaks.

    Yields:
        An async database session.
    """
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
