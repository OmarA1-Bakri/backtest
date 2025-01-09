"""Tests for two-factor authentication."""

import pytest
import pyotp
from fastapi import HTTPException

from core.security.two_factor import two_factor_auth


@pytest.mark.asyncio
async def test_2fa_setup():
    """Test 2FA setup flow."""
    user_id = "test-user-id"

    # Generate secret
    secret, uri, qr_code = await two_factor_auth.generate_secret(user_id)
    assert secret is not None
    assert uri is not None
    assert qr_code is not None
    assert len(secret) == 32  # Base32 secret

    # Verify setup secret is stored
    setup_secret = await two_factor_auth.redis.get(f"2fa_setup:{user_id}")
    assert setup_secret == secret


@pytest.mark.asyncio
async def test_2fa_verification():
    """Test 2FA verification."""
    user_id = "test-user-id"

    # Generate secret
    secret, _, _ = await two_factor_auth.generate_secret(user_id)

    # Generate valid code
    totp = pyotp.TOTP(secret)
    valid_code = totp.now()

    # Verify and activate
    assert await two_factor_auth.verify_and_activate(user_id, valid_code)

    # Check if secret is stored
    active_secret = await two_factor_auth.redis.get(f"2fa_secret:{user_id}")
    assert active_secret == secret

    # Setup secret should be removed
    setup_secret = await two_factor_auth.redis.get(f"2fa_setup:{user_id}")
    assert setup_secret is None


@pytest.mark.asyncio
async def test_invalid_2fa_code():
    """Test invalid 2FA code."""
    user_id = "test-user-id"

    # Generate secret
    await two_factor_auth.generate_secret(user_id)

    # Try invalid code
    with pytest.raises(HTTPException) as exc_info:
        await two_factor_auth.verify_and_activate(user_id, "000000")
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_backup_codes():
    """Test backup codes generation and verification."""
    user_id = "test-user-id"

    # Generate backup codes
    codes = await two_factor_auth.generate_backup_codes(user_id)
    assert len(codes) == 8  # Default count

    # Verify valid code
    assert await two_factor_auth.verify_backup_code(user_id, codes[0])

    # Code should be consumed
    assert not await two_factor_auth.verify_backup_code(user_id, codes[0])

    # Other codes should still work
    assert await two_factor_auth.verify_backup_code(user_id, codes[1])


@pytest.mark.asyncio
async def test_disable_2fa():
    """Test disabling 2FA."""
    user_id = "test-user-id"

    # Set up and activate 2FA
    secret, _, _ = await two_factor_auth.generate_secret(user_id)
    totp = pyotp.TOTP(secret)
    await two_factor_auth.verify_and_activate(user_id, totp.now())

    # Disable 2FA
    assert await two_factor_auth.disable_2fa(user_id)

    # Secret should be removed
    assert not await two_factor_auth.redis.get(f"2fa_secret:{user_id}")

    # Verify should fail
    with pytest.raises(HTTPException):
        await two_factor_auth.verify_code(user_id, totp.now())
