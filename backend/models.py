"""
SQLAlchemy ORM models for the Wave Team Coordination Platform.

Google Services: Models support Cloud Storage file references and Cloud SQL schema.
Security: Password hashes stored separately, no plain-text credentials.
Efficiency: Database indexes on all foreign keys and frequently queried columns.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class VisibilityEnum(str, enum.Enum):
    """Project visibility levels for access control."""

    public = "public"
    private = "private"


class RoleEnum(str, enum.Enum):
    """User roles within a project for permission management."""

    owner = "owner"
    member = "member"


class TaskStatusEnum(str, enum.Enum):
    """Task workflow status for kanban board columns."""

    todo = "todo"
    in_progress = "in_progress"
    done = "done"


class PriorityEnum(str, enum.Enum):
    """Task priority levels for triage and sorting."""

    low = "low"
    medium = "medium"
    high = "high"


class NotificationTypeEnum(str, enum.Enum):
    """Notification categories for user event alerts."""

    task_assigned = "task_assigned"
    comment_added = "comment_added"
    project_invited = "project_invited"
    mention = "mention"


class User(Base):
    """
    User model representing a registered platform user.

    Security: Stores bcrypt-hashed passwords, never plain text.
    Efficiency: Indexed on email for fast authentication lookups.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Unique index on email for fast login lookups
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    # Security: Password stored as bcrypt hash, never plain text
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    status = Column(String(50), default="active")

    # Relationships
    projects = relationship("Project", back_populates="owner")
    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")
    assigned_tasks = relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")
    created_tasks = relationship("Task", foreign_keys="Task.created_by_id", back_populates="created_by")
    comments = relationship("Comment", back_populates="user")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


class Project(Base):
    """
    Project model for team collaboration workspaces.

    Security: Visibility enum controls access (public vs private).
    Efficiency: Indexed on owner_id and name for fast listing.
    """

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Index on name for search and filtering
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Security: Visibility controls who can access the project
    visibility = Column(Enum(VisibilityEnum), default=VisibilityEnum.private)
    # Efficiency: Index on owner_id for fast ownership lookups
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    color = Column(String(50), default="bg-indigo-500")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="projects")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class ProjectMember(Base):
    """
    Join table linking users to projects with role-based access.

    Security: Role field determines permission level (owner vs member).
    Efficiency: Composite index on (project_id, user_id) for fast membership checks.
    """

    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Index on project_id for fast member listing
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    # Efficiency: Index on user_id for fast "my projects" queries
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Security: Role-based access control within projects
    role = Column(Enum(RoleEnum), default=RoleEnum.member)
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Efficiency: Composite index for fast membership lookups
    __table_args__ = (
        Index("ix_project_member_composite", "project_id", "user_id", unique=True),
    )

    # Relationships
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")


class Task(Base):
    """
    Task model for individual work items within a project.

    Security: assignee_id and created_by_id track responsibility.
    Efficiency: Multiple indexes for kanban board queries (status, priority, assignee).
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Index on project_id for fast per-project task listing
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    # Efficiency: Index on status for kanban column queries
    status = Column(Enum(TaskStatusEnum), default=TaskStatusEnum.todo, index=True)
    # Efficiency: Index on priority for sorted task views
    priority = Column(Enum(PriorityEnum), default=PriorityEnum.medium, index=True)
    # Efficiency: Index on assignee_id for "my tasks" dashboard query
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    # Efficiency: Index on created_by_id for creator-based filtering
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # Efficiency: Index on due_date for deadline-based sorting
    due_date = Column(DateTime, nullable=True, index=True)
    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    created_by = relationship("User", foreign_keys=[created_by_id], back_populates="created_tasks")
    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")


class Comment(Base):
    """
    Comment model for task discussions and @mention support.

    Security: Content validated for minimum length via Pydantic schemas.
    Efficiency: Indexed on task_id for fast comment listing per task.
    """

    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Index on task_id for fast per-task comment listing
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    # Efficiency: Index on user_id for user activity queries
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Notification(Base):
    """
    Notification model for real-time user alerts.

    Supports types: task_assigned, comment_added, project_invited, mention.
    Security: Users can only access their own notifications.
    Efficiency: Indexed on user_id for fast per-user notification listing.
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Index on user_id for fast per-user notification queries
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(Enum(NotificationTypeEnum), nullable=False)
    content = Column(Text, nullable=False)
    related_id = Column(Integer, nullable=True)  # task_id or project_id depending on type
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")


class File(Base):
    """
    File model for task attachments stored in Google Cloud Storage.

    Google Services: Files uploaded to GCS bucket via google_services.upload_file_to_gcs.
    Efficiency: Indexed on task_id for fast attachment listing per task.
    """

    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    # Efficiency: Index on task_id for fast per-task file listing
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    # Google Services: URL pointing to Cloud Storage bucket object
    gcs_url = Column(Text, nullable=False)
    # Efficiency: Index on uploaded_by for user file queries
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
