"""Token models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token model."""

    access_token: str
    refresh_token: str
    token_type: str


class TokenPayload(BaseModel):
    """Token payload model."""

    sub: UUID = Field(description="Subject (user ID)")
    exp: float = Field(description="Expiration timestamp")
    type: str = Field(description="Token type (access or refresh)")
    iat: float = Field(description="Issued at timestamp")
