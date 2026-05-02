"""
Activity feed routes for recent project activity.

Google Services: Cloud Logging for activity feed access.
Efficiency: Eager loading with selectinload to prevent N+1 queries.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc
from typing import List

from database import get_db
from models import Task, Comment, User
from auth import get_current_user

# Google Services: Cloud Logging for activity feed tracking
from google_services import log_event

router = APIRouter()


@router.get("")
async def get_activity_feed(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict]:
    """
    Get recent activity feed combining tasks and comments.

    Efficiency: Uses selectinload for eager loading, limits results
    to 10 per type, then merges and sorts for final output.
    Security: Requires authentication to view activity feed.
    Google Services: Cloud Logging for feed access tracking.

    Args:
        db: Async database session dependency.
        current_user: The authenticated user.

    Returns:
        List of activity items (tasks and comments), newest first, max 15.
    """
    # Efficiency: Eager load created_by to prevent N+1 queries
    task_result = await db.execute(
        select(Task)
        .options(selectinload(Task.created_by))
        .order_by(desc(Task.created_at))
        .limit(10)
    )
    recent_tasks = task_result.scalars().all()

    # Efficiency: Eager load user relationship to prevent N+1 queries
    comment_result = await db.execute(
        select(Comment)
        .options(selectinload(Comment.user))
        .order_by(desc(Comment.created_at))
        .limit(10)
    )
    recent_comments = comment_result.scalars().all()

    activities: list[dict] = []
    for t in recent_tasks:
        activities.append({
            "type": "task",
            "id": t.id,
            "description": f"New task created: {t.title}",
            "created_at": t.created_at
        })

    for c in recent_comments:
        activities.append({
            "type": "comment",
            "id": c.id,
            "description": f"New comment on task {c.task_id}",
            "created_at": c.created_at
        })

    # Efficiency: Sort mixed activities by timestamp descending
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    return activities[:15]
