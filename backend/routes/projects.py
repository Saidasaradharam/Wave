"""
Project management routes for creating, listing, and managing projects.

Google Services: Cloud Logging for project lifecycle events.
Security: Access control enforcement for private projects.
Efficiency: Eager loading with selectinload to prevent N+1 queries.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List
from datetime import datetime

from database import get_db
from models import (
    User, Project, ProjectMember, Task,
    RoleEnum, VisibilityEnum, Notification, NotificationTypeEnum,
)
from schemas import (
    ProjectCreate, ProjectOut, ProjectDetailOut, ProjectMemberOut,
    TaskOut, TaskCreate,
)
from auth import get_current_user
from dependencies import verify_project_access, verify_project_member

# Google Services: Cloud Logging for project event tracking
from google_services import log_event

router = APIRouter()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> ProjectOut:
    """
    Create a new project and add the creator as the owner member.

    Security: Only authenticated users can create projects.
    Google Services: Log project creation events.

    Args:
        project: Validated project creation data.
        current_user: The authenticated user creating the project.
        db: Async database session dependency.

    Returns:
        The newly created project.
    """
    new_project = Project(**project.model_dump(), owner_id=current_user.id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)

    # Security: Creator is automatically added as owner member
    owner_member = ProjectMember(
        project_id=new_project.id,
        user_id=current_user.id,
        role=RoleEnum.owner
    )
    db.add(owner_member)
    await db.commit()

    # Google Services: Log project creation for audit trail
    log_event(f"Project created: '{new_project.name}' by {current_user.email}", severity="INFO")

    return new_project


@router.get("", response_model=List[ProjectOut])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[ProjectOut]:
    """
    List all projects the user can access (own, member of, or public).

    Security: Private projects only visible to members/owners.
    Efficiency: Single query with DISTINCT to avoid duplicates.

    Args:
        current_user: The authenticated user.
        db: Async database session dependency.

    Returns:
        List of accessible projects.
    """
    # Efficiency: Single query combines public + owned + member projects
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
) -> ProjectDetailOut:
    """
    Get detailed project information including members.

    Security: Access verified via verify_project_access dependency.
    Efficiency: Members eagerly loaded in dependency to prevent N+1.

    Args:
        project_id: The ID of the project to retrieve.
        project: The project loaded by the access verification dependency.

    Returns:
        Project details including member list.
    """
    return project


@router.post("/{project_id}/join", status_code=status.HTTP_200_OK)
async def join_project(
    project_id: int,
    project: Project = Depends(verify_project_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Join a public project as a member.

    Security: Only public projects can be joined directly.

    Args:
        project_id: The ID of the project to join.
        project: The project verified for access.
        current_user: The authenticated user joining.
        db: Async database session dependency.

    Returns:
        Success message.

    Raises:
        HTTPException 403: If project is private.
        HTTPException 400: If already a member.
    """
    # Security: Block direct joining of private projects
    if project.visibility != VisibilityEnum.public:
        raise HTTPException(status_code=403, detail="Can only join public projects directly")

    # Efficiency: Index-backed membership check
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

    # Google Services: Log member join event
    log_event(f"User {current_user.email} joined project '{project.name}'", severity="INFO")

    return {"message": "Successfully joined project"}


@router.post("/{project_id}/invite", status_code=status.HTTP_200_OK)
async def invite_member(
    project_id: int,
    email: str = Query(..., description="Email of the user to invite"),
    project: Project = Depends(verify_project_member),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Invite a user to the project by email address.

    Security: Only project members/owners can invite new members.
    Google Services: Cloud Logging for invitation audit trail.

    Args:
        project_id: The ID of the project.
        email: Email address of the user to invite.
        project: The project verified for member access.
        current_user: The authenticated user sending the invite.
        db: Async database session dependency.

    Returns:
        Success message.

    Raises:
        HTTPException 404: If invited user not found.
        HTTPException 400: If user is already a member.
    """
    # Security: Validate invited user exists
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Efficiency: Index-backed duplicate membership check
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

    # Create notification for the invited user
    notification = Notification(
        user_id=user.id,
        type=NotificationTypeEnum.project_invited,
        content=f"{current_user.name} invited you to project '{project.name}'",
        related_id=project.id
    )
    db.add(notification)

    await db.commit()

    # Google Services: Log invitation event
    log_event(f"User {email} invited to project '{project.name}' by {current_user.email}", severity="INFO")

    return {"message": "User invited successfully"}


@router.get("/{project_id}/tasks", response_model=List[TaskOut])
async def list_project_tasks(
    project_id: int,
    project: Project = Depends(verify_project_access),
    db: AsyncSession = Depends(get_db)
) -> List[TaskOut]:
    """
    Get all tasks for a project, ordered by status and position.

    Efficiency: Uses selectinload to eagerly load assignee and creator,
    preventing N+1 queries when serializing task responses.
    Security: Access verified via verify_project_access dependency.

    Args:
        project_id: The ID of the project.
        project: The project verified for access.
        db: Async database session dependency.

    Returns:
        List of tasks with loaded relationships.
    """
    # Efficiency: Eager load relationships to prevent N+1 queries
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
) -> TaskOut:
    """
    Create a new task within a project.

    Security: Only project members can create tasks.
    Efficiency: Auto-positions task at end of its status column.
    Google Services: Cloud Logging for task creation events.

    Args:
        project_id: The ID of the project.
        task_in: Validated task creation data.
        project: The project verified for member access.
        current_user: The authenticated user creating the task.
        db: Async database session dependency.

    Returns:
        The newly created task with loaded relationships.
    """
    # Efficiency: Find max position in one query to auto-position
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

    # Efficiency: Reload with eagerly loaded relationships
    query = select(Task).options(
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == new_task.id)
    result = await db.execute(query)

    # Google Services: Log task creation event
    log_event(f"Task created: '{new_task.title}' in project {project_id}", severity="INFO")

    return result.scalar_one()
