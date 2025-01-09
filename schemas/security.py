"""Security-related schemas."""

from typing import List
from pydantic import BaseModel, EmailStr


class TwoFactorSetup(BaseModel):
    """2FA setup response schema."""

    secret: str
    uri: str
    qr_code: bytes
    backup_codes: List[str]


class TwoFactorVerify(BaseModel):
    """2FA verification request schema."""

    code: str


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""

    email: EmailStr


class PasswordResetVerify(BaseModel):
    """Password reset verification schema."""

    token: str
    new_password: str
