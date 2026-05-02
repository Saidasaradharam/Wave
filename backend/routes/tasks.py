"""
Task management routes for updating, moving, assigning, and deleting tasks.

Google Services: Cloud Logging for task lifecycle tracking.
Security: Project membership verification for all task operations.
Efficiency: Eager loading with selectinload to prevent N+1 queries.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List

from database import get_db
from models import User, Task, ProjectMember, Project, Notification, NotificationTypeEnum, TaskStatusEnum
from schemas import TaskUpdate, TaskOut
from auth import get_current_user

# Google Services: Cloud Logging for task event tracking
from google_services import log_event

router = APIRouter()


@router.get("/assigned-to-me", response_model=List[TaskOut])
async def get_assigned_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[TaskOut]:
    """
    Get all tasks assigned to the current user across ALL projects.

    Efficiency: Uses selectinload to eagerly load relationships and prevent N+1 queries.
    Security: Only returns tasks assigned to the authenticated user.

    Args:
        db: Async database session dependency.
        current_user: The authenticated user.

    Returns:
        List of tasks assigned to the user, ordered by status and position.
    """
    # Efficiency: Eager load all relationships in one query
    query = (
        select(Task)
        .options(
            selectinload(Task.created_by),
            selectinload(Task.assignee),
            selectinload(Task.project),
        )
        .where(Task.assignee_id == current_user.id)
        .order_by(Task.status, Task.position)
    )
    result = await db.execute(query)
    return result.scalars().all()


class TaskMove(BaseModel):
    """Schema for task drag-and-drop move operations."""

    new_status: TaskStatusEnum
    new_position: int


@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TaskOut:
    """
    Update a task's fields (title, description, status, priority, assignee).

    Security: Verifies caller is a project member before allowing edits.
    Google Services: Cloud Logging for task assignment notifications.

    Args:
        task_id: The ID of the task to update.
        task_in: Partial update data (only provided fields are updated).
        db: Async database session dependency.
        current_user: The authenticated user making the update.

    Returns:
        The updated task with loaded relationships.

    Raises:
        HTTPException 404: If task not found.
        HTTPException 403: If user is not a project member.
    """
    # Efficiency: Eager load relationships in initial query
    result = await db.execute(select(Task).options(
        selectinload(Task.project),
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Security: Verify project membership before allowing edits
    if task.project.owner_id != current_user.id:
        member_check = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == task.project_id,
                ProjectMember.user_id == current_user.id
            )
        )
        if not member_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Must be a member to edit task")

    update_data = task_in.model_dump(exclude_unset=True)

    # Check assignment change and create notification
    if "assignee_id" in update_data and update_data["assignee_id"] != task.assignee_id:
        if update_data["assignee_id"]:
            notification = Notification(
                user_id=update_data["assignee_id"],
                type=NotificationTypeEnum.task_assigned,
                content=f"{current_user.name} assigned you to task '{task.title}'",
                related_id=task.id
            )
            db.add(notification)
            # Google Services: Log task assignment event
            log_event(f"Task '{task.title}' assigned to user {update_data['assignee_id']}", severity="INFO")

    for key, value in update_data.items():
        setattr(task, key, value)

    await db.commit()
    await db.refresh(task)

    # Efficiency: Reload with eagerly loaded relationships for response
    query = select(Task).options(
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == task.id)
    result = await db.execute(query)
    return result.scalar_one()


@router.put("/{task_id}/move", response_model=TaskOut)
async def move_task(
    task_id: int,
    move_in: TaskMove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> TaskOut:
    """
    Move a task to a new status column and/or position (drag-and-drop).

    Security: Only authenticated users can move tasks.
    Efficiency: Direct status/position update without full reload.
    Google Services: Cloud Logging for task status changes.

    Args:
        task_id: The ID of the task to move.
        move_in: The target status and position.
        db: Async database session dependency.
        current_user: The authenticated user performing the move.

    Returns:
        The updated task.

    Raises:
        HTTPException 404: If task not found.
    """
    # Efficiency: Eager load relationships for response serialization
    result = await db.execute(select(Task).options(
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    old_status = task.status
    task.status = move_in.new_status
    task.position = move_in.new_position

    await db.commit()
    await db.refresh(task)

    # Google Services: Log status change for activity tracking
    if old_status != move_in.new_status:
        log_event(f"Task '{task.title}' moved from {old_status} to {move_in.new_status}", severity="INFO")

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> None:
    """
    Delete a task permanently.

    Security: Verifies caller is a project member or owner before deletion.
    Google Services: Cloud Logging for task deletion audit trail.

    Args:
        task_id: The ID of the task to delete.
        db: Async database session dependency.
        current_user: The authenticated user performing the deletion.

    Returns:
        None (204 No Content).

    Raises:
        HTTPException 404: If task not found.
        HTTPException 403: If user lacks permission to delete.
    """
    # Efficiency: Load task with project relationship for permission check
    result = await db.execute(
        select(Task).options(selectinload(Task.project)).where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Security: Verify user is project member or owner before allowing deletion
    if task.project.owner_id != current_user.id:
        member_check = await db.execute(
            select(ProjectMember).where(
                ProjectMember.project_id == task.project_id,
                ProjectMember.user_id == current_user.id
            )
        )
        if not member_check.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Must be a project member to delete tasks")

    # Google Services: Log task deletion for audit trail
    log_event(f"Task '{task.title}' deleted by {current_user.email}", severity="WARNING")

    await db.delete(task)
    await db.commit()
    return None
