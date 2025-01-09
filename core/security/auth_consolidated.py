"""Authentication and authorization module."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from redis import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.settings import settings
from database.session import get_session
from database.models.user import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

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


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> Optional[User]:
    """Authenticate user by email and password.

    Args:
        session: Database session
        email: User email
        password: User password

    Returns:
        Optional[User]: User if authenticated, None otherwise
    """
    user = await get_user_by_email(session, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    subject: str,
    data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT access token.

    Args:
        subject: Token subject (usually user ID)
        data: Additional data to encode in token
        expires_delta: Token expiration time

    Returns:
        str: JWT token
    """
    to_encode = data.copy() if data else {}
    to_encode["sub"] = subject

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT refresh token.

    Args:
        subject: Token subject (usually user ID)
        data: Additional data to encode in token
        expires_delta: Token expiration time

    Returns:
        str: JWT token
    """
    to_encode = data.copy() if data else {}
    to_encode["sub"] = subject

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "refresh"})

    token = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

    # Store refresh token in Redis
    redis.setex(
        f"refresh_token:{token}",
        int(expire.timestamp() - datetime.utcnow().timestamp()),
        "valid",
    )

    return token


def decode_token(token: str, expected_type: str = "access") -> Dict[str, Any]:
    """Decode and verify JWT token.

    Args:
        token: JWT token
        expected_type: Expected token type ("access" or "refresh")

    Returns:
        dict: Token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        if not payload.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
            )

        if payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {expected_type}",
            )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_session)
) -> User:
    """Get current authenticated user.

    Args:
        token: JWT token from request
        db: Database session

    Returns:
        User: Current authenticated user

    Raises:
        HTTPException: If user not found or token invalid
    """
    payload = decode_token(token)
    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current active user

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current authenticated superuser.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Current authenticated superuser

    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


def verify_refresh_token(token: str) -> str:
    """Verify refresh token and return user ID if valid.

    Args:
        token: Refresh token

    Returns:
        str: User ID from token

    Raises:
        HTTPException: If token is invalid or expired
    """
    payload = decode_token(token, expected_type="refresh")
    token_key = f"refresh_token:{token}"

    if not redis.exists(token_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return payload["sub"]


def revoke_refresh_token(token: str) -> None:
    """Revoke a refresh token.

    Args:
        token: Refresh token to revoke
    """
    redis.delete(f"refresh_token:{token}")


async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    """Get user by email.

    Args:
        session: Database session
        email: User email

    Returns:
        Optional[User]: User if found, None otherwise
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def check_permission(user: User, required_permission: str) -> bool:
    """Check if user has required permission.

    Args:
        user: User to check permissions for
        required_permission: Required permission name

    Returns:
        bool: True if user has permission, False otherwise
    """
    # Superusers have all permissions
    if user.is_superuser:
        return True

    # Get all permissions from user's roles
    user_permissions = set()
    for role in user.roles:
        user_permissions.update(perm.name for perm in role.permissions)

    return required_permission in user_permissions


def requires_permission(permission: str):
    """Dependency for checking permission.

    Args:
        permission: Required permission name

    Returns:
        Callable: Dependency function
    """

    async def permission_checker(current_user: User = Depends(get_current_active_user)):
        if not await check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Not enough permissions. Required: {permission}",
            )
        return current_user

    return permission_checker


def requires_role(role_name: str):
    """Dependency for checking role.

    Args:
        role_name: Required role name

    Returns:
        Callable: Dependency function
    """

    async def role_checker(current_user: User = Depends(get_current_active_user)):
        # Superusers have all roles
        if current_user.is_superuser:
            return current_user

        user_roles = {role.name for role in current_user.roles}
        if role_name not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role not found: {role_name}",
            )
        return current_user

    return role_checker
