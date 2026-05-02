import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from main import app, Base
from database import get_db

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)

async def override_get_db():
    async with TestingSessionLocal() as db:
        yield db

app.dependency_overrides[get_db] = override_get_db

import asyncio

@pytest.fixture(autouse=True)
def setup_db():
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    async def drop_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
    asyncio.run(init_db())
    yield
    asyncio.run(drop_db())

client = TestClient(app)

def test_create_user_success():
    """Test successful user creation"""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "name": "Test User",
        "password": "password123"
    })
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"

def test_create_user_invalid_email():
    """Test user creation with invalid email"""
    response = client.post("/api/auth/register", json={
        "email": "invalid-email",
        "name": "Test User",
        "password": "password123"
    })
    assert response.status_code == 422  # Validation error

def test_login_success():
    """Test successful login"""
    client.post("/api/auth/register", json={
        "email": "login@example.com",
        "name": "Login User",
        "password": "password123"
    })
    response = client.post("/api/auth/login", json={
        "email": "login@example.com",
        "password": "password123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_create_task(monkeypatch):
    """Test creating a task requires auth"""
    # Create user and login
    client.post("/api/auth/register", json={
        "email": "task@example.com",
        "name": "Task User",
        "password": "password123"
    })
    login_res = client.post("/api/auth/login", json={
        "email": "task@example.com",
        "password": "password123"
    })
    token = login_res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/api/tasks", json={
        "title": "New Task",
        "priority": "high",
        "status": "todo"
    }, headers=headers)
    assert response.status_code == 201
    assert response.json()["title"] == "New Task"
    
    # List tasks
    list_res = client.get("/api/tasks", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
