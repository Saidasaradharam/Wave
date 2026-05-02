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

router = APIRouter()

@router.get("/{task_id}/comments", response_model=List[CommentOut])
async def list_comments(
    task_id: int, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """List comments for a task"""
    query = select(Comment).options(selectinload(Comment.user)).where(Comment.task_id == task_id).order_by(Comment.created_at.asc())
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/{task_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def add_comment(
    task_id: int, 
    comment_in: CommentCreate, 
    db: AsyncSession = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """Add a comment with mention parsing"""
    # Verify task exists
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
        
    new_comment = Comment(task_id=task_id, user_id=current_user.id, content=comment_in.content)
    db.add(new_comment)
    
    # Parse mentions like @UserName
    mentions = set(re.findall(r'@(\w+)', comment_in.content))
    if mentions:
        for name in mentions:
            # Simple match by name
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
                
    await db.commit()
    await db.refresh(new_comment)
    
    # Load user relation
    result = await db.execute(select(Comment).options(selectinload(Comment.user)).where(Comment.id == new_comment.id))
    return result.scalar_one()
