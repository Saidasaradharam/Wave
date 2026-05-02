from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from database import get_db
from models import User, Project, ProjectMember, RoleEnum, VisibilityEnum, Notification, NotificationTypeEnum
from schemas import ProjectCreate, ProjectOut, ProjectDetailOut, ProjectMemberOut
from auth import get_current_user
from dependencies import verify_project_access, verify_project_member

router = APIRouter()

@router.post("/", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new project and add the creator as the owner"""
    new_project = Project(**project.model_dump(), owner_id=current_user.id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    
    # Add creator as owner member
    owner_member = ProjectMember(
        project_id=new_project.id,
        user_id=current_user.id,
        role=RoleEnum.owner
    )
    db.add(owner_member)
    await db.commit()
    
    return new_project

@router.get("/", response_model=List[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all projects user is a member of or are public"""
    query = select(Project).outerjoin(ProjectMember).where(
        (Project.visibility == VisibilityEnum.public) |
        (Project.owner_id == current_user.id) |
        (ProjectMember.user_id == current_user.id)
    ).distinct()
    
    result = await db.execute(query)
    projects = result.scalars().all()
    return projects

@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: int,
    project: Project = Depends(verify_project_access)
):
    """Get project details including members"""
    return project

@router.post("/{project_id}/join", status_code=status.HTTP_200_OK)
async def join_project(
    project_id: int,
    project: Project = Depends(verify_project_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Join a public project"""
    if project.visibility != VisibilityEnum.public:
        raise HTTPException(status_code=403, detail="Can only join public projects directly")
        
    # Check if already a member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == current_user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member")
        
    member = ProjectMember(
        project_id=project_id,
        user_id=current_user.id,
        role=RoleEnum.member
    )
    db.add(member)
    await db.commit()
    return {"message": "Successfully joined project"}

@router.post("/{project_id}/invite", status_code=status.HTTP_200_OK)
async def invite_member(
    project_id: int,
    email: str,
    project: Project = Depends(verify_project_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Invite a user to the project by email"""
    # Find user by email
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if already a member
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user.id
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User is already a member")
        
    # Add member
    member = ProjectMember(
        project_id=project_id,
        user_id=user.id,
        role=RoleEnum.member
    )
    db.add(member)
    
    # Create notification
    notification = Notification(
        user_id=user.id,
        type=NotificationTypeEnum.project_invited,
        content=f"{current_user.name} invited you to project '{project.name}'",
        related_id=project.id
    )
    db.add(notification)
    
    await db.commit()
    return {"message": "User invited successfully"}

from schemas import TaskOut, TaskCreate
from models import Task

@router.get("/{project_id}/tasks", response_model=List[TaskOut])
async def list_project_tasks(
    project_id: int,
    project: Project = Depends(verify_project_access),
    db: AsyncSession = Depends(get_db)
):
    """Get all tasks for a project ordered by position"""
    query = select(Task).options(
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.project_id == project_id).order_by(Task.status, Task.position)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{project_id}/tasks", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_project_task(
    project_id: int,
    task_in: TaskCreate,
    project: Project = Depends(verify_project_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a task in a project"""
    # Get max position for the given status to append at the end
    result = await db.execute(
        select(Task).where(Task.project_id == project_id, Task.status == task_in.status)
        .order_by(Task.position.desc())
        .limit(1)
    )
    max_task = result.scalar_one_or_none()
    new_position = (max_task.position + 1) if max_task else 0
    
    new_task = Task(
        **task_in.model_dump(exclude={"position"}),
        project_id=project_id,
        created_by_id=current_user.id,
        position=new_position
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Reload with relationships
    query = select(Task).options(
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == new_task.id)
    result = await db.execute(query)
    return result.scalar_one()
