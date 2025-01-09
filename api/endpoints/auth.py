"""Authentication endpoints."""

from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.auth_consolidated import (
    authenticate_user,
    get_current_active_user,
)
from core.security.token_manager import token_manager
from core.security.session import session_manager
from core.security.password_policy import password_policy
from database.session import get_session
from database.models.user import User
from schemas.token import Token, RefreshToken
from core.security.rate_limit import RateLimiter

router = APIRouter()
rate_limiter = RateLimiter(requests_per_minute=5)  # Strict limit for auth endpoints


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Login user and return access and refresh tokens.

    Args:
        request: Request object
        response: Response object
        form_data: OAuth2 password request form
        db: Database session

    Returns:
        Token: Access and refresh tokens

    Raises:
        HTTPException: If authentication fails
    """
    # Check rate limit
    await rate_limiter.check_rate_limit(form_data.username)

    # Authenticate user
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create tokens
    access_token, refresh_token = await token_manager.create_tokens(
        str(user.id),
        additional_data={
            "username": user.username,
            "email": user.email,
            "is_superuser": user.is_superuser,
        },
    )

    # Create session
    session_id = await session_manager.create_session(
        str(user.id),
        {
            "username": user.username,
            "email": user.email,
            "ip_address": request.client.host,
            "user_agent": request.headers.get("user-agent"),
        },
    )

    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=86400,  # 24 hours
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: RefreshToken,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Refresh access token using refresh token.

    Args:
        refresh_token: Current refresh token
        db: Database session

    Returns:
        Token: New access and refresh tokens

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        # Get new token pair
        access_token, new_refresh_token = await token_manager.refresh_tokens(
            refresh_token.refresh_token
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not refresh token",
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    refresh_token: RefreshToken,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Logout user by revoking refresh token and ending session.

    Args:
        request: Request object
        response: Response object
        refresh_token: Current refresh token
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    try:
        # Revoke refresh token
        await token_manager.revoke_token(refresh_token.refresh_token)

        # End session
        session_id = request.cookies.get("session_id")
        if session_id:
            await session_manager.end_session(session_id)
            response.delete_cookie(
                key="session_id",
                httponly=True,
                secure=True,
                samesite="strict",
            )

        return {"message": "Successfully logged out"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging out",
        )


@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Logout user from all sessions.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    try:
        # End all user sessions
        await session_manager.end_all_user_sessions(str(current_user.id))

        return {"message": "Successfully logged out from all sessions"}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error logging out from all sessions",
        )
