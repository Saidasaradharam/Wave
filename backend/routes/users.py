from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from database import get_db
from models import User
from schemas import UserOut
from auth import get_current_user

router = APIRouter()

@router.get("", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """List team members"""
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users
