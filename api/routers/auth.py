"""Authentication router."""

from typing import Annotated, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from redis import asyncio as aioredis

from api.deps import get_session
from core.config.settings import settings
from core.security.auth_consolidated import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_current_active_user,
    get_current_active_superuser,
    get_password_hash,
    verify_refresh_token,
)
from database.models.user import User
from api.schemas.auth import Token, UserCreate, UserRead, UserUpdate

router = APIRouter()

# Redis connection
redis = aioredis.Redis(
    host=settings.BACKTEST_REDIS_HOST,
    port=settings.BACKTEST_REDIS_PORT,
    db=settings.BACKTEST_REDIS_DB,
    password=settings.BACKTEST_REDIS_PASSWORD,
    decode_responses=True,
)


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Dict[str, str]:
    """Login user."""
    user = await authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Store refresh token in Redis
    await redis.set(
        f"refresh_token:{user.email}",
        refresh_token,
        ex=settings.BACKTEST_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Dict[str, str]:
    """Refresh access token."""
    user_email = await verify_refresh_token(refresh_token)
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if refresh token is in Redis
    stored_token = await redis.get(f"refresh_token:{user_email}")
    if not stored_token or stored_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user_email})
    new_refresh_token = create_refresh_token(data={"sub": user_email})

    # Update refresh token in Redis
    await redis.set(
        f"refresh_token:{user_email}",
        new_refresh_token,
        ex=settings.BACKTEST_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/register", response_model=UserRead)
async def register(
    user_in: UserCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Dict[str, Any]:
    """Register new user."""
    # Check if user already exists
    stmt = select(User).where(User.email == user_in.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create new user
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return user


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Dict[str, Any]:
    """Get current user."""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_user_me(
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> Dict[str, Any]:
    """Update current user."""
    if user_in.password is not None:
        hashed_password = get_password_hash(user_in.password)
        current_user.hashed_password = hashed_password
    if user_in.email is not None:
        current_user.email = user_in.email
    if user_in.is_active is not None:
        current_user.is_active = user_in.is_active
    await session.commit()
    await session.refresh(current_user)

    return current_user


@router.get("/superuser", response_model=UserRead)
async def read_user_me_superuser(
    current_user: Annotated[User, Depends(get_current_active_superuser)],
) -> Dict[str, Any]:
    """Get current superuser."""
    return current_user
