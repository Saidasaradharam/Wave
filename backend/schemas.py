"""
Pydantic schemas for request/response validation.

Security: Input validation with strict field constraints (min/max length, email format).
Google Services: Schemas support Google Cloud service data types (GCS URLs, etc.).
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import VisibilityEnum, RoleEnum, TaskStatusEnum, PriorityEnum, NotificationTypeEnum


# ===========================================================================
# User Schemas
# ===========================================================================

class UserCreate(BaseModel):
    """
    Schema for user registration requests.

    Security: Enforces email format validation, minimum password length,
    and alphanumeric name constraint to prevent injection attacks.
    """

    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    # Security: Minimum password length enforcement
    password: str = Field(..., min_length=6)

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        """Security: Validate name contains only safe alphanumeric characters."""
        if not v.replace(' ', '').isalnum():
            raise ValueError('Name can only contain letters and numbers')
        return v


class UserLogin(BaseModel):
    """
    Schema for user login requests.

    Security: Email format validation, optional Firebase token for SSO.
    Google Services: Firebase Authentication token support.
    """

    email: EmailStr
    password: str
    # Google Services: Firebase Authentication token for SSO login
    firebase_token: Optional[str] = None


class UserOut(BaseModel):
    """
    Schema for public user profile responses.

    Security: Excludes password_hash from serialization to prevent credential leakage.
    """

    id: int
    email: str
    name: str
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """
    Schema for JWT authentication token response.

    Security: Contains access token and token type for Bearer authentication.
    """

    access_token: str
    token_type: str
    user: UserOut


# ===========================================================================
# Project Schemas
# ===========================================================================

class ProjectBase(BaseModel):
    """
    Base schema for project data with shared validation rules.

    Security: Visibility enum restricts to valid options only.
    """

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    # Security: Controlled visibility options (public/private)
    visibility: VisibilityEnum = VisibilityEnum.private
    color: str = "bg-indigo-500"


class ProjectCreate(ProjectBase):
    """Schema for project creation requests. Inherits all base validations."""

    pass


class ProjectOut(ProjectBase):
    """
    Schema for project responses with server-generated fields.

    Efficiency: Uses from_attributes for direct ORM model serialization.
    """

    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectMemberBase(BaseModel):
    """Base schema for project membership data."""

    project_id: int
    user_id: int
    # Security: Role controls permission level within project
    role: RoleEnum = RoleEnum.member


class ProjectMemberOut(ProjectMemberBase):
    """Schema for project member responses including user details."""

    id: int
    joined_at: datetime
    user: UserOut

    model_config = ConfigDict(from_attributes=True)


class ProjectDetailOut(ProjectOut):
    """
    Extended project schema with member list for detail views.

    Efficiency: Members eagerly loaded via selectinload in the query.
    """

    members: List[ProjectMemberOut] = []


# ===========================================================================
# Task Schemas
# ===========================================================================

class TaskBase(BaseModel):
    """
    Base schema for task data with kanban board field validation.

    Security: Status and priority limited to enum values to prevent injection.
    """

    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.todo
    priority: PriorityEnum = PriorityEnum.medium
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    position: int = 0


class TaskCreate(TaskBase):
    """Schema for task creation requests. Inherits all base validations."""

    pass


class TaskUpdate(BaseModel):
    """
    Schema for partial task updates (PATCH-like semantics).

    Efficiency: Uses exclude_unset=True in model_dump for partial updates,
    only modifying fields that were explicitly provided.
    """

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = None


class TaskOut(TaskBase):
    """
    Schema for task responses with loaded relationships.

    Efficiency: Assignee and created_by eagerly loaded via selectinload.
    """

    id: int
    project_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime

    assignee: Optional[UserOut] = None
    created_by: UserOut

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# Comment Schemas
# ===========================================================================

class CommentCreate(BaseModel):
    """
    Schema for comment creation with @mention support.

    Security: Minimum content length prevents empty comments.
    """

    content: str = Field(..., min_length=1)


class CommentOut(BaseModel):
    """Schema for comment responses including author information."""

    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime
    user: UserOut

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# Notification Schemas
# ===========================================================================

class NotificationBase(BaseModel):
    """Base schema for notification data with type categorization."""

    type: NotificationTypeEnum
    content: str
    related_id: Optional[int] = None
    read: bool = False


class NotificationOut(NotificationBase):
    """Schema for notification responses with server-generated timestamps."""

    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ===========================================================================
# File Schemas
# ===========================================================================

class FileOut(BaseModel):
    """
    Schema for file attachment responses.

    Google Services: gcs_url points to Google Cloud Storage bucket object.
    """

    id: int
    task_id: int
    filename: str
    # Google Services: URL to file in Cloud Storage bucket
    gcs_url: str
    uploaded_by: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
