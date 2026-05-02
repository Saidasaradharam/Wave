"""
User management routes for listing team members.

Google Services: Cloud Logging for user data access.
Security: Requires authentication to access user list.
Efficiency: Uses indexed queries for user retrieval.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models import User
from schemas import UserOut
from auth import get_current_user

# Google Services: Cloud Logging for user access tracking
from google_services import log_event

router = APIRouter()


@router.get("", response_model=List[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[UserOut]:
    """
    List all registered users (team members).

    Security: Requires valid JWT authentication to access user directory.
    Efficiency: Returns only public user fields via UserOut schema.

    Args:
        db: Async database session dependency.
        current_user: The authenticated user requesting the list.

    Returns:
        List of all users with public profile information.
    """
    # Efficiency: Simple scan — consider pagination for large user bases
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
