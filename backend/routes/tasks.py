import os
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import User, Task, ProjectMember, Project, Notification, NotificationTypeEnum, TaskStatusEnum
from schemas import TaskUpdate, TaskOut
from auth import get_current_user
from pydantic import BaseModel
from typing import List

router = APIRouter()


@router.get("/assigned-to-me", response_model=List[TaskOut])
async def get_assigned_tasks(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all tasks assigned to the current user across ALL projects.
    Efficiency: Uses selectinload to eagerly load relationships and prevent N+1 queries.
    """
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
    new_status: TaskStatusEnum
    new_position: int

@router.put("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: int, 
    task_in: TaskUpdate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Update a task"""
    result = await db.execute(select(Task).options(
        selectinload(Task.project),
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Verify member status for project
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
    
    # Check assignment notification
    if "assignee_id" in update_data and update_data["assignee_id"] != task.assignee_id:
        if update_data["assignee_id"]:
            notification = Notification(
                user_id=update_data["assignee_id"],
                type=NotificationTypeEnum.task_assigned,
                content=f"{current_user.name} assigned you to task '{task.title}'",
                related_id=task.id
            )
            db.add(notification)
            
    for key, value in update_data.items():
        setattr(task, key, value)
        
    await db.commit()
    await db.refresh(task)
    
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
):
    """Move a task to a new status/position (Drag and Drop)"""
    result = await db.execute(select(Task).options(
        selectinload(Task.created_by),
        selectinload(Task.assignee)
    ).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Simple position update - full gap reordering could be added here
    task.status = move_in.new_status
    task.position = move_in.new_position
    
    await db.commit()
    await db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Delete a task"""
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return None
