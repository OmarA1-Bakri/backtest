"""Authentication and authorization module."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from core.config.settings import settings
from database.session import get_session
from database.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Redis connection
redis = Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    password=(
        settings.REDIS_PASSWORD.get_secret_value() if settings.REDIS_PASSWORD else None
    ),
    decode_responses=True,
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token.

    Args:
        token: JWT token

    Returns:
        dict: Token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify token type and user ID
        if payload.get("type") != "access":
            raise credentials_exception

        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Get user from database
        stmt = select(User).where(User.id == UUID(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            raise credentials_exception

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
            )

        return user

    except jwt.JWTError:
        raise credentials_exception


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current authenticated superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )
    return current_user


async def verify_refresh_token(token: str) -> Optional[str]:
    """Verify refresh token and return user ID if valid."""
    try:
        # Check if token exists in Redis
        user_id = await redis.get(f"refresh_token:{token}")
        if not user_id:
            return None

        # Verify token payload
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        if payload.get("type") != "refresh":
            return None

        return user_id.decode()

    except (jwt.JWTError, Exception):
        return None


async def revoke_refresh_token(token: str) -> bool:
    """Revoke a refresh token."""
    try:
        return bool(await redis.delete(f"refresh_token:{token}"))
    except Exception:
        return False


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email.

    Args:
        session: Database session
        email: User email

    Returns:
        Optional[User]: User if found, None otherwise
    """
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()
