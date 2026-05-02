import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Google Services: Secret Manager integration for database credentials
from google_services import get_secret

def get_database_url() -> str:
    """
    Retrieve database URL from environment or Google Cloud Secret Manager.
    Security: Never hardcode database credentials.
    Google Services: Secret Manager integration.
    """
    # Efficiency: Check environment variable first (fast path)
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url

    # Google Services: Try Secret Manager for production credentials
    secret_url = get_secret("database-url")
    if secret_url:
        return secret_url

    # Fallback to local SQLite for development
    logging.info("Using local SQLite database (wave.db)")
    return "sqlite+aiosqlite:///./wave.db"


DATABASE_URL = get_database_url()

# Efficiency: Database connection pooling
engine_args = {"echo": False}
if "sqlite" not in DATABASE_URL:
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_async_engine(DATABASE_URL, **engine_args)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    """Dependency to get async database session."""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()
