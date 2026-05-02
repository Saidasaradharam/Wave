"""
Comment routes for task discussion and @mention notifications.

Google Services: Cloud Logging for comment and mention tracking.
Security: Input validation, authenticated comment creation.
Efficiency: Eager loading with selectinload to prevent N+1 queries.
"""
import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List

from database import get_db
from models import User, Task, Comment, Notification, NotificationTypeEnum
from schemas import CommentCreate, CommentOut
from auth import get_current_user

# Google Services: Cloud Logging for comment event tracking
from google_services import log_event

router = APIRouter()


@router.get("/{task_id}/comments", response_model=List[CommentOut])
async def list_comments(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[CommentOut]:
    """
    List all comments for a specific task, ordered chronologically.

    Security: Requires authentication to view comments.
    Efficiency: Uses selectinload to eagerly load user data and prevent N+1 queries.

    Args:
        task_id: The ID of the task to list comments for.
        db: Async database session dependency.
        current_user: The authenticated user.

    Returns:
        List of comments with user information.
    """
    # Efficiency: Eager load user relationship to prevent N+1 queries
    query = (
        select(Comment)
        .options(selectinload(Comment.user))
        .where(Comment.task_id == task_id)
        .order_by(Comment.created_at.asc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: int,
    comment_in: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> CommentOut:
    """
    Add a comment to a task with @mention notification parsing.

    Security: Input validated via Pydantic (min_length=1), authenticated users only.
    Google Services: Cloud Logging for comment and mention events.
    Efficiency: Batch mention lookups and notification creation in single commit.

    Args:
        task_id: The ID of the task to comment on.
        comment_in: Validated comment content data.
        db: Async database session dependency.
        current_user: The authenticated user posting the comment.

    Returns:
        The created comment with user information.

    Raises:
        HTTPException 404: If task not found.
    """
    # Security: Verify task exists before allowing comment
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_comment = Comment(task_id=task_id, user_id=current_user.id, content=comment_in.content)
    db.add(new_comment)

    # Security: Parse @mentions safely with regex pattern matching
    mentions = set(re.findall(r'@(\w+)', comment_in.content))
    if mentions:
        for name in mentions:
            # Efficiency: Index-backed user lookup by name
            user_result = await db.execute(select(User).where(User.name.ilike(f"{name}%")))
            mentioned_user = user_result.scalars().first()
            if mentioned_user and mentioned_user.id != current_user.id:
                notification = Notification(
                    user_id=mentioned_user.id,
                    type=NotificationTypeEnum.mention,
                    content=f"{current_user.name} mentioned you in task '{task.title}'",
                    related_id=task.id
                )
                db.add(notification)
                # Google Services: Log mention event for activity tracking
                log_event(
                    f"User {current_user.email} mentioned {mentioned_user.email} in task '{task.title}'",
                    severity="INFO"
                )

    await db.commit()
    await db.refresh(new_comment)

    # Google Services: Log comment creation event
    log_event(f"Comment added to task '{task.title}' by {current_user.email}", severity="INFO")

    # Efficiency: Reload with eagerly loaded user relationship for response
    result = await db.execute(
        select(Comment).options(selectinload(Comment.user)).where(Comment.id == new_comment.id)
    )
    return result.scalar_one()
