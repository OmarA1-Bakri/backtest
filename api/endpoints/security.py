"""Security-related endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.security.auth_consolidated import get_current_active_user
from core.security.two_factor import two_factor_auth
from core.security.password_reset import password_reset
from core.security.password_policy import password_policy
from database.session import get_session
from database.models.user import User
from schemas.security import (
    TwoFactorSetup,
    TwoFactorVerify,
    PasswordResetRequest,
    PasswordResetVerify,
)

router = APIRouter()


# 2FA endpoints
@router.post("/2fa/setup", response_model=TwoFactorSetup)
async def setup_2fa(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Set up 2FA for user.

    Args:
        current_user: Current authenticated user

    Returns:
        TwoFactorSetup: 2FA setup data
    """
    # Generate 2FA secret and QR code
    secret, uri, qr_code = await two_factor_auth.generate_secret(str(current_user.id))

    # Generate backup codes
    backup_codes = await two_factor_auth.generate_backup_codes(str(current_user.id))

    return {
        "secret": secret,
        "uri": uri,
        "qr_code": qr_code,
        "backup_codes": backup_codes,
    }


@router.post("/2fa/verify")
async def verify_2fa(
    data: TwoFactorVerify,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Verify and activate 2FA.

    Args:
        data: Verification data
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    await two_factor_auth.verify_and_activate(str(current_user.id), data.code)
    return {"message": "2FA activated successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """Disable 2FA.

    Args:
        current_user: Current authenticated user

    Returns:
        dict: Success message
    """
    await two_factor_auth.disable_2fa(str(current_user.id))
    return {"message": "2FA disabled successfully"}


# Password reset endpoints
@router.post("/password/reset-request")
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Request password reset.

    Args:
        data: Reset request data
        db: Database session

    Returns:
        dict: Success message
    """
    # Find user by email
    stmt = select(User).where(User.email == data.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user:
        # Generate reset token
        token = await password_reset.create_reset_token(str(user.id), user.email)

        # TODO: Send reset email with token
        # For now, just return token (in production, never return token)
        return {"reset_token": token}

    # Always return success to prevent email enumeration
    return {"message": "If email exists, reset instructions will be sent"}


@router.post("/password/reset-verify")
async def verify_password_reset(
    data: PasswordResetVerify,
    db: AsyncSession = Depends(get_session),
) -> Any:
    """Verify reset token and set new password.

    Args:
        data: Reset verification data
        db: Database session

    Returns:
        dict: Success message
    """
    # Validate new password
    is_valid, errors = password_policy.validate_password(data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"password_errors": errors},
        )

    # Reset password
    await password_reset.reset_password(data.token, data.new_password, db)
    return {"message": "Password reset successfully"}
