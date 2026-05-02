"""
Tests for Wave Team Coordination Platform.
Covers: Authentication, Projects, Tasks, Comments, Mentions, Notifications.
Google Services: All tests run without Google Cloud credentials.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from main import app, Base
from database import get_db
import asyncio

# Efficiency: In-memory SQLite for fast test execution
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine,
    class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """Test dependency override for database sessions."""
    async with TestingSessionLocal() as db:
        yield db


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create a shared event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_db(event_loop):
    """Create and drop all tables for each test."""
    async def init_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    event_loop.run_until_complete(init_db())
    yield
    event_loop.run_until_complete(drop_db())


client = TestClient(app)


# ──────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────

def register_user(email: str, name: str, password: str = "password123") -> dict:
    """Register a user and return the response JSON."""
    res = client.post("/api/auth/register", json={
        "email": email, "name": name, "password": password
    })
    return res


def login_user(email: str, password: str = "password123") -> dict:
    """Login a user and return auth headers."""
    res = client.post("/api/auth/login", json={
        "email": email, "password": password
    })
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def create_authenticated_user(email: str, name: str) -> dict:
    """Register + login, return auth headers."""
    register_user(email, name)
    return login_user(email)


# ──────────────────────────────────────────────────────
# 1. Authentication Tests
# ──────────────────────────────────────────────────────

class TestAuthentication:
    """Security: Test user registration and login flows."""

    def test_register_success(self):
        """Test successful user registration."""
        res = register_user("newuser@example.com", "New User")
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "newuser@example.com"
        assert data["name"] == "New User"
        assert "password" not in data  # Security: password not exposed

    def test_register_duplicate_email(self):
        """Test that duplicate emails are rejected."""
        register_user("dup@example.com", "First")
        res = register_user("dup@example.com", "Second")
        assert res.status_code == 400
        assert "already registered" in res.json()["detail"].lower()

    def test_register_invalid_email(self):
        """Test that invalid emails are rejected. Security: Input validation."""
        res = client.post("/api/auth/register", json={
            "email": "not-an-email", "name": "Test", "password": "password123"
        })
        assert res.status_code == 400

    def test_register_short_password(self):
        """Test that short passwords are rejected. Security: Password policy."""
        res = client.post("/api/auth/register", json={
            "email": "short@example.com", "name": "Test", "password": "123"
        })
        assert res.status_code == 400

    def test_login_success(self):
        """Test successful login returns JWT token."""
        register_user("login@example.com", "Login User")
        res = client.post("/api/auth/login", json={
            "email": "login@example.com", "password": "password123"
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "login@example.com"

    def test_login_wrong_password(self):
        """Test that wrong password returns 401."""
        register_user("wrongpw@example.com", "Wrong PW")
        res = client.post("/api/auth/login", json={
            "email": "wrongpw@example.com", "password": "wrongpassword"
        })
        assert res.status_code == 401

    def test_login_nonexistent_user(self):
        """Test that login with non-existent email returns 401."""
        res = client.post("/api/auth/login", json={
            "email": "noone@example.com", "password": "password123"
        })
        assert res.status_code == 401

    def test_protected_route_without_token(self):
        """Security: Verify protected routes reject unauthenticated requests."""
        res = client.get("/api/projects")
        assert res.status_code in (401, 403)  # HTTPBearer rejects unauthenticated requests


# ──────────────────────────────────────────────────────
# 2. Project Tests
# ──────────────────────────────────────────────────────

class TestProjects:
    """Test project CRUD, joining, and invitations."""

    def test_create_public_project(self):
        """Test creating a public project."""
        headers = create_authenticated_user("projowner@example.com", "ProjOwner")
        res = client.post("/api/projects", json={
            "name": "My Public Project",
            "description": "A test project",
            "visibility": "public"
        }, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "My Public Project"
        assert data["visibility"] == "public"

    def test_create_private_project(self):
        """Test creating a private project."""
        headers = create_authenticated_user("privowner@example.com", "PrivOwner")
        res = client.post("/api/projects", json={
            "name": "Secret Project",
            "visibility": "private"
        }, headers=headers)
        assert res.status_code == 201
        assert res.json()["visibility"] == "private"

    def test_list_projects(self):
        """Test listing projects (user sees own + public)."""
        headers = create_authenticated_user("lister@example.com", "Lister")
        client.post("/api/projects", json={
            "name": "Lister Project", "visibility": "public"
        }, headers=headers)

        res = client.get("/api/projects", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) >= 1

    def test_get_project_detail(self):
        """Test getting project details with members."""
        headers = create_authenticated_user("detailowner@example.com", "DetailOwner")
        create_res = client.post("/api/projects", json={
            "name": "Detail Project", "visibility": "private"
        }, headers=headers)
        proj_id = create_res.json()["id"]

        detail_res = client.get(f"/api/projects/{proj_id}", headers=headers)
        assert detail_res.status_code == 200
        assert detail_res.json()["owner_id"] is not None
        assert len(detail_res.json()["members"]) >= 1  # Owner is a member

    def test_join_public_project(self):
        """Test joining a public project."""
        owner_headers = create_authenticated_user("joinowner@example.com", "JoinOwner")
        member_headers = create_authenticated_user("joiner@example.com", "Joiner")

        create_res = client.post("/api/projects", json={
            "name": "Open Project", "visibility": "public"
        }, headers=owner_headers)
        proj_id = create_res.json()["id"]

        join_res = client.post(f"/api/projects/{proj_id}/join", headers=member_headers)
        assert join_res.status_code == 200

    def test_cannot_join_private_project(self):
        """Test that users cannot directly join private projects."""
        owner_headers = create_authenticated_user("privjoinowner@example.com", "PrivJoinOwner")
        member_headers = create_authenticated_user("privjoiner@example.com", "PrivJoiner")

        create_res = client.post("/api/projects", json={
            "name": "Locked Project", "visibility": "private"
        }, headers=owner_headers)
        proj_id = create_res.json()["id"]

        join_res = client.post(f"/api/projects/{proj_id}/join", headers=member_headers)
        assert join_res.status_code == 403

    def test_invite_to_private_project(self):
        """Test owner can invite users to private projects."""
        owner_headers = create_authenticated_user("invowner@example.com", "InvOwner")
        register_user("invitee@example.com", "Invitee")

        create_res = client.post("/api/projects", json={
            "name": "Invite Project", "visibility": "private"
        }, headers=owner_headers)
        proj_id = create_res.json()["id"]

        invite_res = client.post(
            f"/api/projects/{proj_id}/invite?email=invitee@example.com",
            headers=owner_headers
        )
        assert invite_res.status_code == 200

    def test_duplicate_join_rejected(self):
        """Test that joining a project twice is rejected."""
        owner_headers = create_authenticated_user("dupjoinowner@example.com", "DupJoinOwner")
        member_headers = create_authenticated_user("dupjoiner@example.com", "DupJoiner")

        create_res = client.post("/api/projects", json={
            "name": "Dup Join Project", "visibility": "public"
        }, headers=owner_headers)
        proj_id = create_res.json()["id"]

        client.post(f"/api/projects/{proj_id}/join", headers=member_headers)
        dup_res = client.post(f"/api/projects/{proj_id}/join", headers=member_headers)
        assert dup_res.status_code == 400


# ──────────────────────────────────────────────────────
# 3. Task Tests
# ──────────────────────────────────────────────────────

class TestTasks:
    """Test task creation, updates, and drag-and-drop moves."""

    def _setup_project(self):
        """Helper: create a user and project, return (headers, project_id)."""
        headers = create_authenticated_user("taskuser@example.com", "TaskUser")
        res = client.post("/api/projects", json={
            "name": "Task Project", "visibility": "private"
        }, headers=headers)
        return headers, res.json()["id"]

    def test_create_task(self):
        """Test creating a task inside a project."""
        headers, proj_id = self._setup_project()
        res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Build feature X",
            "status": "todo",
            "priority": "high"
        }, headers=headers)
        assert res.status_code == 201
        data = res.json()
        assert data["title"] == "Build feature X"
        assert data["status"] == "todo"
        assert data["priority"] == "high"
        assert data["project_id"] == proj_id

    def test_list_project_tasks(self):
        """Test listing tasks for a project."""
        headers, proj_id = self._setup_project()
        client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Task 1", "status": "todo", "priority": "low"
        }, headers=headers)
        client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Task 2", "status": "in_progress", "priority": "medium"
        }, headers=headers)

        res = client.get(f"/api/projects/{proj_id}/tasks", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_move_task_status(self):
        """Test drag-and-drop: moving a task to a new status."""
        headers, proj_id = self._setup_project()
        create_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Move me", "status": "todo", "priority": "medium"
        }, headers=headers)
        task_id = create_res.json()["id"]

        move_res = client.put(f"/api/tasks/{task_id}/move", json={
            "new_status": "in_progress", "new_position": 0
        }, headers=headers)
        assert move_res.status_code == 200
        assert move_res.json()["status"] == "in_progress"

    def test_move_task_to_done(self):
        """Test moving a task to done status."""
        headers, proj_id = self._setup_project()
        create_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Complete me", "status": "todo", "priority": "low"
        }, headers=headers)
        task_id = create_res.json()["id"]

        move_res = client.put(f"/api/tasks/{task_id}/move", json={
            "new_status": "done", "new_position": 0
        }, headers=headers)
        assert move_res.status_code == 200
        assert move_res.json()["status"] == "done"

    def test_update_task(self):
        """Test updating task fields (title, priority, assignee)."""
        headers, proj_id = self._setup_project()
        create_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Original Title", "status": "todo", "priority": "low"
        }, headers=headers)
        task_id = create_res.json()["id"]

        update_res = client.put(f"/api/tasks/{task_id}", json={
            "title": "Updated Title", "priority": "high"
        }, headers=headers)
        assert update_res.status_code == 200
        assert update_res.json()["title"] == "Updated Title"
        assert update_res.json()["priority"] == "high"

    def test_delete_task(self):
        """Test deleting a task."""
        headers, proj_id = self._setup_project()
        create_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Delete me", "status": "todo", "priority": "low"
        }, headers=headers)
        task_id = create_res.json()["id"]

        del_res = client.delete(f"/api/tasks/{task_id}", headers=headers)
        assert del_res.status_code == 204

    def test_assign_task_creates_notification(self):
        """Test that assigning a task creates a notification for the assignee."""
        owner_headers = create_authenticated_user("assigner@example.com", "Assigner")
        assignee_res = register_user("assignee@example.com", "Assignee")
        assignee_id = assignee_res.json()["id"]
        assignee_headers = login_user("assignee@example.com")

        # Create project and add assignee as member
        proj_res = client.post("/api/projects", json={
            "name": "Assign Project", "visibility": "public"
        }, headers=owner_headers)
        proj_id = proj_res.json()["id"]
        client.post(f"/api/projects/{proj_id}/join", headers=assignee_headers)

        # Create task
        task_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Assign me", "status": "todo", "priority": "medium"
        }, headers=owner_headers)
        task_id = task_res.json()["id"]

        # Assign task
        client.put(f"/api/tasks/{task_id}", json={
            "assignee_id": assignee_id
        }, headers=owner_headers)

        # Verify notification created
        notif_res = client.get("/api/notifications", headers=assignee_headers)
        assert notif_res.status_code == 200
        notifications = notif_res.json()
        assert any("assigned" in n["content"].lower() for n in notifications)

    def test_assigned_to_me(self):
        """Test the /tasks/assigned-to-me endpoint returns tasks across all projects."""
        owner_headers = create_authenticated_user("myowner@example.com", "MyOwner")
        assignee_res = register_user("myassignee@example.com", "MyAssignee")
        assignee_id = assignee_res.json()["id"]
        assignee_headers = login_user("myassignee@example.com")

        # Create two projects, assign a task in each to the same user
        for i, name in enumerate(["Project Alpha", "Project Beta"]):
            proj_res = client.post("/api/projects", json={
                "name": name, "visibility": "public"
            }, headers=owner_headers)
            proj_id = proj_res.json()["id"]
            client.post(f"/api/projects/{proj_id}/join", headers=assignee_headers)

            task_res = client.post(f"/api/projects/{proj_id}/tasks", json={
                "title": f"Task in {name}", "status": "todo", "priority": "high"
            }, headers=owner_headers)
            task_id = task_res.json()["id"]
            client.put(f"/api/tasks/{task_id}", json={
                "assignee_id": assignee_id
            }, headers=owner_headers)

        # Fetch assigned tasks
        res = client.get("/api/tasks/assigned-to-me", headers=assignee_headers)
        assert res.status_code == 200
        assert len(res.json()) == 2
        titles = [t["title"] for t in res.json()]
        assert "Task in Project Alpha" in titles
        assert "Task in Project Beta" in titles


# ──────────────────────────────────────────────────────
# 4. Comment & Mention Tests
# ──────────────────────────────────────────────────────

class TestComments:
    """Test comments and @mention parsing."""

    def _setup_task(self):
        """Helper: create user, project, task. Return (headers, task_id)."""
        headers = create_authenticated_user("commenter@example.com", "Commenter")
        proj_res = client.post("/api/projects", json={
            "name": "Comment Project", "visibility": "private"
        }, headers=headers)
        proj_id = proj_res.json()["id"]
        task_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Comment Task", "status": "todo", "priority": "medium"
        }, headers=headers)
        return headers, task_res.json()["id"]

    def test_add_comment(self):
        """Test adding a comment to a task."""
        headers, task_id = self._setup_task()
        res = client.post(f"/api/tasks/{task_id}/comments", json={
            "content": "This looks good!"
        }, headers=headers)
        assert res.status_code == 201
        assert res.json()["content"] == "This looks good!"

    def test_list_comments(self):
        """Test listing comments on a task."""
        headers, task_id = self._setup_task()
        client.post(f"/api/tasks/{task_id}/comments", json={
            "content": "First comment"
        }, headers=headers)
        client.post(f"/api/tasks/{task_id}/comments", json={
            "content": "Second comment"
        }, headers=headers)

        res = client.get(f"/api/tasks/{task_id}/comments", headers=headers)
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_mention_creates_notification(self):
        """Test that @mentioning a user in a comment creates a notification."""
        # Create the commenter and their project/task
        commenter_headers = create_authenticated_user("mentioner@example.com", "Mentioner")
        register_user("mentioned@example.com", "MentionedUser")
        mentioned_headers = login_user("mentioned@example.com")

        proj_res = client.post("/api/projects", json={
            "name": "Mention Project", "visibility": "private"
        }, headers=commenter_headers)
        proj_id = proj_res.json()["id"]

        task_res = client.post(f"/api/projects/{proj_id}/tasks", json={
            "title": "Mention Task", "status": "todo", "priority": "medium"
        }, headers=commenter_headers)
        task_id = task_res.json()["id"]

        # Post comment with @mention
        client.post(f"/api/tasks/{task_id}/comments", json={
            "content": "Hey @MentionedUser check this out!"
        }, headers=commenter_headers)

        # Verify notification
        notif_res = client.get("/api/notifications", headers=mentioned_headers)
        assert notif_res.status_code == 200
        notifications = notif_res.json()
        assert any("mentioned" in n["content"].lower() for n in notifications)


# ──────────────────────────────────────────────────────
# 5. Notification Tests
# ──────────────────────────────────────────────────────

class TestNotifications:
    """Test notification fetching and marking as read."""

    def test_list_notifications_empty(self):
        """Test listing notifications when user has none."""
        headers = create_authenticated_user("nonotif@example.com", "NoNotif")
        res = client.get("/api/notifications", headers=headers)
        assert res.status_code == 200
        assert res.json() == []

    def test_invite_creates_notification(self):
        """Test that project invitation creates a notification."""
        owner_headers = create_authenticated_user("notifowner@example.com", "NotifOwner")
        register_user("notifinvitee@example.com", "NotifInvitee")
        invitee_headers = login_user("notifinvitee@example.com")

        proj_res = client.post("/api/projects", json={
            "name": "Notif Project", "visibility": "private"
        }, headers=owner_headers)
        proj_id = proj_res.json()["id"]

        client.post(
            f"/api/projects/{proj_id}/invite?email=notifinvitee@example.com",
            headers=owner_headers
        )

        res = client.get("/api/notifications", headers=invitee_headers)
        assert res.status_code == 200
        assert len(res.json()) > 0
        assert "invited" in res.json()[0]["content"].lower()

    def test_mark_notification_read(self):
        """Test marking a notification as read."""
        owner_headers = create_authenticated_user("readowner@example.com", "ReadOwner")
        register_user("reader@example.com", "Reader")
        reader_headers = login_user("reader@example.com")

        proj_res = client.post("/api/projects", json={
            "name": "Read Project", "visibility": "private"
        }, headers=owner_headers)
        proj_id = proj_res.json()["id"]

        client.post(
            f"/api/projects/{proj_id}/invite?email=reader@example.com",
            headers=owner_headers
        )

        # Get the notification
        notifs = client.get("/api/notifications", headers=reader_headers).json()
        notif_id = notifs[0]["id"]

        # Mark as read
        mark_res = client.put(f"/api/notifications/{notif_id}/read", headers=reader_headers)
        assert mark_res.status_code == 200
        assert mark_res.json()["read"] is True


# ──────────────────────────────────────────────────────
# 6. Health Check & Google Services Fallback Test
# ──────────────────────────────────────────────────────

class TestHealthCheck:
    """Test that the app starts and responds without Google Cloud credentials."""

    def test_root_endpoint(self):
        """Google Services: App starts without credentials."""
        res = client.get("/")
        assert res.status_code == 200
        assert "Wave API" in res.json()["message"]
