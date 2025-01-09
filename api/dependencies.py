"""API dependencies."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.auth_consolidated import (
    decode_token,
    get_user_by_email,
    get_current_user,
    get_current_active_user,
)
from database.session import get_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/auth/login")

# Re-export dependencies
__all__ = [
    "get_current_user",
    "get_current_active_user",
    "oauth2_scheme",
    "get_session",
]
