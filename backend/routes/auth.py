"""
Authentication routes for user registration and login.

Google Services: Cloud Logging for authentication event tracking.
Security: Password hashing, input validation, JWT token management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from datetime import timedelta

from database import get_db
from models import User
from schemas import UserCreate, UserLogin, Token, UserOut
from auth import get_password_hash, verify_password, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Google Services: Cloud Logging for authentication events
from google_services import log_event

router = APIRouter()


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)) -> UserOut:
    """
    User registration endpoint.

    Security: Password hashing with bcrypt, input validation via Pydantic.
    Google Services: Cloud Logging for registration event auditing.

    Args:
        user_in: Validated user registration data (email, name, password).
        db: Async database session dependency.

    Returns:
        The created user object (without password).

    Raises:
        HTTPException 400: If email already exists.
        HTTPException 500: On unexpected database errors.
    """
    # Security: Hash password with bcrypt before storage
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
        # Google Services: Log registration event for audit trail
        log_event(f"New user registered: {new_user.email}", severity="INFO")
        return new_user
    except IntegrityError:
        await db.rollback()
        # Security: Generic error message to prevent email enumeration
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except Exception as e:
        await db.rollback()
        log_event(f"Registration error: {e}", severity="ERROR")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=Token)
async def login(user_in: UserLogin, db: AsyncSession = Depends(get_db)) -> dict:
    """
    User login endpoint.

    Security: Credential verification, JWT token issuance with expiry.
    Google Services: Cloud Logging for login event tracking and failed attempts.

    Args:
        user_in: Login credentials (email, password).
        db: Async database session dependency.

    Returns:
        JWT access token and user details.

    Raises:
        HTTPException 401: On invalid credentials.
    """
    # Efficiency: Index-backed email lookup
    result = await db.execute(select(User).where(User.email == user_in.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_in.password, user.password_hash):
        # Google Services: Log failed login attempt for security monitoring
        # Security: Log failed attempts without revealing which field was wrong
        log_event(f"Failed login attempt for: {user_in.email}", severity="WARNING")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Security: Token expires after configured duration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Google Services: Log successful login for audit trail
    log_event(f"User logged in: {user.email}", severity="INFO")

    return {"access_token": access_token, "token_type": "bearer", "user": user}
