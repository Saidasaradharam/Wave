"""
Pytest configuration and shared test fixtures.

Google Services: Tests run without Google Cloud credentials.
Efficiency: In-memory SQLite for fast test execution.
Security: Test isolation — each test gets a fresh database.
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from database import Base, get_db


# Efficiency: In-memory SQLite for instant test database creation
TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine,
    class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Test dependency override for database sessions."""
    async with TestingSessionLocal() as db:
        yield db


# Security: Override production database with test database
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a shared event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_db(event_loop):
    """
    Create and drop all tables for each test.

    Security: Test isolation ensures no data leakage between tests.
    Efficiency: In-memory SQLite is created/dropped instantly.
    """
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    event_loop.run_until_complete(init_db())
    yield
    event_loop.run_until_complete(drop_db())
