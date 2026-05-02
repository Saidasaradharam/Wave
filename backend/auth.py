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

# Security: Use environment variables for JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-dev")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

security = HTTPBearer()


# Security: Password hashing with bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt. Security: Salted hashing."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a signed JWT token. Security: Token expiry enforcement."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current user. Validates standard JWT or Firebase token.
    Google Services: Firebase Authentication integration.
    """
    try:
        token = credentials.credentials

        # Google Services: Try Firebase validation first if available and token looks like Firebase
        if FIREBASE_ENABLED and len(token) > 200:
            try:
                from google_services import firebase_auth
                if firebase_auth:
                    decoded_token = firebase_auth.verify_id_token(token)
                    email = decoded_token.get("email")
                    if email:
                        result = await db.execute(select(User).where(User.email == email))
                        user = result.scalar_one_or_none()
                        if user:
                            return user
            except Exception:
                pass  # Fall back to local JWT

        # Security: Local JWT validation
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
