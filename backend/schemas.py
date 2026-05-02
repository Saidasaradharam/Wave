from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime

# Security: Input validation using Pydantic
class UserCreate(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=6)

    @validator('name')
    def validate_name(cls, v):
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

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserOut

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = Field(default="medium")
    status: str = Field(default="todo")
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[int] = None
    due_date: Optional[datetime] = None

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1)

class CommentOut(BaseModel):
    id: int
    task_id: int
    user_id: int
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

class FileOut(BaseModel):
    id: int
    task_id: int
    filename: str
    gcs_url: str
    uploaded_by: int
    uploaded_at: datetime

    class Config:
        from_attributes = True

class TaskOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    priority: str
    status: str
    assigned_to: Optional[int]
    created_by: int
    due_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
