"""Token schemas."""

from typing import Optional
from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload schema."""

    sub: str
    username: Optional[str] = None
    email: Optional[str] = None
    is_superuser: bool = False
    type: str  # "access" or "refresh"
    exp: int
    iat: int
    jti: str


class RefreshToken(BaseModel):
    """Refresh token request schema."""

    refresh_token: str
