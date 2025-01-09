"""Authentication schemas."""

from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """Token response schema."""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(..., description="Token type (e.g., 'bearer')")


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str = Field(..., description="Subject (user ID)")
    exp: datetime = Field(..., description="Token expiration time")
    type: str = Field(..., description="Token type")
    iat: datetime = Field(..., description="Token issued at time")


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr = Field(..., description="User's email address")


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., description="User's password", min_length=8)


class UserUpdate(BaseModel):
    """User update schema."""

    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(
        None, description="User's new password", min_length=8
    )
    is_active: Optional[bool] = Field(None, description="Whether the user is active")


class UserRead(UserBase):
    """User response schema."""

    id: UUID = Field(..., description="User's UUID")
    is_active: bool = Field(..., description="Whether the user is active")
    is_superuser: bool = Field(..., description="Whether the user is a superuser")

    class Config:
        """Pydantic config."""

        from_attributes = True
        json_encoders = {UUID: str}
