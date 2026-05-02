from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, Token, UserOut
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from google.cloud import logging as cloud_logging

router = APIRouter()

# Security: Google Cloud Logging
try:
    logging_client = cloud_logging.Client()
    logger = logging_client.logger('auth-logs')
except Exception:
    import logging
    logger = logging.getLogger("auth-logs")

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """User registration endpoint"""
    hashed_password = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email,
        name=user_in.name,
        password_hash=hashed_password
    )
    db.add(new_user)
    try:
        await db.commit()
        await db.refresh(new_user)
        try:
            logger.log_text(f"New user registered: {new_user.email}", severity="INFO")
        except AttributeError:
            logger.info(f"New user registered: {new_user.email}")
        return new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)):
    """User login endpoint"""
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_in.password, user.password_hash):
        try:
            logger.log_text(f"Failed login attempt for: {user_in.email}", severity="WARNING")
        except AttributeError:
            logger.warning(f"Failed login attempt for: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    try:
        logger.log_text(f"User logged in: {user.email}", severity="INFO")
    except AttributeError:
        logger.info(f"User logged in: {user.email}")
        
    return {"access_token": access_token, "token_type": "bearer", "user": user}
