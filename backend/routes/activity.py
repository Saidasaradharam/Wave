from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from database import get_db
from models import Task, Comment, User
from auth import get_current_user

router = APIRouter()

@router.get("")
async def get_activity_feed(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get recent activity feed (tasks created and comments)"""
    # Fetch recent tasks
    task_result = await db.execute(
        select(Task).order_by(desc(Task.created_at)).limit(10)
    )
    recent_tasks = task_result.scalars().all()
    
    # Fetch recent comments
    comment_result = await db.execute(
        select(Comment).order_by(desc(Comment.created_at)).limit(10)
    )
    recent_comments = comment_result.scalars().all()
    
    activities = []
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
        
    # Sort mixed activities by created_at descending
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    return activities[:15]
