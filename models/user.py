"""User models."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Boolean, select
from sqlalchemy.dialects.postgresql import UUID
import uuid
from pydantic import BaseModel, EmailStr, constr

from core.database.base import Base


class User(Base):
    """SQLAlchemy User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    last_login = Column(DateTime, nullable=True)

    @classmethod
    async def get_by_username(cls, db, username: str):
        """Get user by username."""
        stmt = select(cls).where(cls.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Pydantic models for request/response validation
class UserBase(BaseModel):
    email: EmailStr
    username: constr(min_length=3, max_length=50)


class UserCreate(UserBase):
    password: constr(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_superuser: bool
    last_login: Optional[datetime]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
