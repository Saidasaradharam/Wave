import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from google.cloud import secretmanager

def get_database_url() -> str:
    """
    Retrieve database URL from Google Cloud Secret Manager.
    Security: Never hardcode database credentials.
    Google Services: Secret Manager integration.
    """
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    try:
        client = secretmanager.SecretManagerServiceClient()
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id")
        name = f"projects/{project_id}/secrets/database-url/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception:
        return "sqlite+aiosqlite:///./app.db"

DATABASE_URL = get_database_url()

# Efficiency: Database connection pooling
engine_args = {"echo": False}
if "sqlite" not in DATABASE_URL:
    engine_args["pool_size"] = 10
    engine_args["max_overflow"] = 20

engine = create_async_engine(DATABASE_URL, **engine_args)
SessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def get_db():
    """Dependency to get async database session."""
    async with SessionLocal() as db:
        try:
            yield db
        finally:
            await db.close()

from sqlalchemy.orm import declarative_base
Base = declarative_base()
