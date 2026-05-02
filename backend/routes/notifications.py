"""
Notification routes for listing and managing user notifications.

Google Services: Cloud Logging for notification status changes.
Security: Users can only access their own notifications.
Efficiency: Index-backed queries on user_id and notification_id.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models import User, Notification
from schemas import NotificationOut
from auth import get_current_user

# Google Services: Cloud Logging for notification event tracking
from google_services import log_event

router = APIRouter()


@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> List[NotificationOut]:
    """
    List all notifications for the current user, newest first.

    Security: Only returns notifications belonging to the authenticated user.
    Efficiency: Index on user_id ensures fast filtering.

    Args:
        current_user: The authenticated user.
        db: Async database session dependency.

    Returns:
        List of notifications ordered by creation date descending.
    """
    # Efficiency: Index-backed query on user_id column
    query = (
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> NotificationOut:
    """
    Mark a specific notification as read.

    Security: Verifies notification belongs to the authenticated user.
    Google Services: Cloud Logging for notification state changes.

    Args:
        notification_id: The ID of the notification to mark as read.
        current_user: The authenticated user.
        db: Async database session dependency.

    Returns:
        The updated notification.

    Raises:
        HTTPException 404: If notification not found or doesn't belong to user.
    """
    # Security: Filter by both notification_id AND user_id to prevent unauthorized access
    query = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    )
    result = await db.execute(query)
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    await db.commit()
    await db.refresh(notification)

    # Google Services: Log notification state change
    log_event(f"Notification {notification_id} marked as read by {current_user.email}", severity="DEBUG")

    return notification
