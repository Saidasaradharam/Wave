from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from models import VisibilityEnum, RoleEnum, TaskStatusEnum, PriorityEnum, NotificationTypeEnum

# Security: Input validation using Pydantic
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)

    @field_validator('name')
    def validate_name(cls, v: str) -> str:
        if not v.replace(' ', '').isalnum():
            raise ValueError('Name can only contain letters and numbers')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    firebase_token: Optional[str] = None

class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: str
    status: str

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    visibility: VisibilityEnum = VisibilityEnum.private
    color: str = "bg-indigo-500"

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ProjectMemberBase(BaseModel):
    project_id: int
    user_id: int
    role: RoleEnum = RoleEnum.member

class ProjectMemberOut(ProjectMemberBase):
    id: int
    joined_at: datetime
    user: UserOut

    model_config = ConfigDict(from_attributes=True)

class ProjectDetailOut(ProjectOut):
    members: List[ProjectMemberOut] = []

# Task Schemas
class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    status: TaskStatusEnum = TaskStatusEnum.todo
    priority: PriorityEnum = PriorityEnum.medium
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    position: int = 0

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[PriorityEnum] = None
    assignee_id: Optional[int] = None
    due_date: Optional[datetime] = None
    position: Optional[int] = None

class TaskOut(TaskBase):
    id: int
    project_id: int
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    
    assignee: Optional[UserOut] = None
    created_by: UserOut
    
    model_config = ConfigDict(from_attributes=True)

# Comment Schemas
class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)

class CommentOut(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime
    user: UserOut

    model_config = ConfigDict(from_attributes=True)

# Notification Schemas
class NotificationBase(BaseModel):
    type: NotificationTypeEnum
    content: str
    related_id: Optional[int] = None
    read: bool = False

class NotificationOut(NotificationBase):
    id: int
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# File Schemas
class FileOut(BaseModel):
    id: int
    task_id: int
    filename: str
    gcs_url: str
    uploaded_by: int
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)
