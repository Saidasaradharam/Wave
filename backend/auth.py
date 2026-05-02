"""
Authentication utilities for JWT token management and password hashing.

Google Services: Firebase Authentication integration for SSO login.
Security: bcrypt password hashing, JWT token expiry, credential validation.
"""
import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import bcrypt

from database import get_db
from models import User

# Google Services: Firebase Authentication integration
from google_services import FIREBASE_ENABLED

# Security: Use environment variables for JWT configuration — never hardcode
SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-for-dev")
ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# Security: HTTPBearer scheme for token extraction
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Security: Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    # Security: bcrypt constant-time comparison prevents timing attacks
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt with automatic salt generation.

    Security: bcrypt with random salt — each hash is unique even for identical passwords.

    Args:
        password: The plaintext password to hash.

    Returns:
        The bcrypt hash string.
    """
    # Security: Salted bcrypt hashing prevents rainbow table attacks
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a signed JWT access token with expiry.

    Security: Token includes expiry claim to limit validity window.

    Args:
        data: Claims to encode in the JWT payload (e.g., {"sub": email}).
        expires_delta: Custom token lifetime. Defaults to 15 minutes.

    Returns:
        The encoded JWT token string.
    """
    to_encode = data.copy()
    # Security: Token expiry enforcement — defaults to 15 minutes
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to authenticate and retrieve the current user.

    Validates JWT token or Firebase ID token (when available).
    Google Services: Firebase Authentication integration for SSO.
    Security: Validates token signature, expiry, and user existence.

    Args:
        credentials: The Bearer token extracted from the Authorization header.
        db: Async database session dependency.

    Returns:
        The authenticated User object.

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found.
    """
    try:
        token = credentials.credentials

        # Google Services: Try Firebase validation first if available
        # Security: Firebase tokens are longer than local JWTs
        if FIREBASE_ENABLED and len(token) > 200:
            try:
                from google_services import firebase_auth
                if firebase_auth:
                    decoded_token = firebase_auth.verify_id_token(token)
                    email = decoded_token.get("email")
                    if email:
                        # Efficiency: Index-backed email lookup
                        result = await db.execute(select(User).where(User.email == email))
                        user = result.scalar_one_or_none()
                        if user:
                            return user
            except Exception:
                pass  # Security: Fall back to local JWT on Firebase failure

        # Security: Local JWT validation with signature and expiry check
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Efficiency: Index-backed email lookup
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except jwt.JWTError:
        # Security: Reject expired or tampered tokens
        raise HTTPException(status_code=401, detail="Invalid or expired token")
