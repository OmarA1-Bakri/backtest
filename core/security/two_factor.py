"""Two-factor authentication implementation."""

import base64
import hmac
import time
from typing import Tuple, List
import pyotp
from qrcode import QRCode
from io import BytesIO
import secrets

from fastapi import HTTPException, status
from redis.asyncio import Redis

from core.config.settings import settings
from logger import logger


class TwoFactorAuth:
    """Two-factor authentication manager."""

    def __init__(self):
        """Initialize 2FA manager."""
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=(
                settings.REDIS_PASSWORD.get_secret_value()
                if settings.REDIS_PASSWORD
                else None
            ),
            decode_responses=True,
        )
        self.issuer = settings.PROJECT_NAME

    async def generate_secret(self, user_id: str) -> Tuple[str, str, bytes]:
        """Generate new TOTP secret for user.

        Args:
            user_id: User ID

        Returns:
            Tuple[str, str, bytes]: (secret, provisioning_uri, qr_code)
        """
        # Generate secret
        secret = pyotp.random_base32()

        # Create TOTP object
        totp = pyotp.TOTP(secret)

        # Generate provisioning URI for QR code
        provisioning_uri = totp.provisioning_uri(name=user_id, issuer_name=self.issuer)

        # Generate QR code
        qr = QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        # Create QR code image
        img_buffer = BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(img_buffer)
        qr_code = img_buffer.getvalue()

        # Store secret temporarily (10 minutes to set up)
        await self.redis.set(f"2fa_setup:{user_id}", secret, ex=600)  # 10 minutes

        return secret, provisioning_uri, qr_code

    async def verify_and_activate(self, user_id: str, code: str) -> bool:
        """Verify setup code and activate 2FA.

        Args:
            user_id: User ID
            code: TOTP code

        Returns:
            bool: True if verified and activated

        Raises:
            HTTPException: If setup secret not found or verification fails
        """
        # Get setup secret
        setup_key = f"2fa_setup:{user_id}"
        secret = await self.redis.get(setup_key)

        if not secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup expired or not initiated",
            )

        # Verify code
        totp = pyotp.TOTP(secret)
        if not totp.verify(code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code",
            )

        # Store active secret
        await self.redis.set(f"2fa_secret:{user_id}", secret)
        await self.redis.delete(setup_key)

        return True

    async def verify_code(self, user_id: str, code: str) -> bool:
        """Verify TOTP code.

        Args:
            user_id: User ID
            code: TOTP code

        Returns:
            bool: True if verified

        Raises:
            HTTPException: If 2FA not set up or verification fails
        """
        # Get user's secret
        secret = await self.redis.get(f"2fa_secret:{user_id}")
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA not set up for user",
            )

        # Verify code
        totp = pyotp.TOTP(secret)
        if not totp.verify(code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code",
            )

        return True

    async def disable_2fa(self, user_id: str) -> bool:
        """Disable 2FA for user.

        Args:
            user_id: User ID

        Returns:
            bool: True if disabled
        """
        # Remove 2FA secret
        result = await self.redis.delete(f"2fa_secret:{user_id}")
        return bool(result)

    async def generate_backup_codes(self, user_id: str, count: int = 8) -> List[str]:
        """Generate backup codes for user.

        Args:
            user_id: User ID
            count: Number of backup codes to generate

        Returns:
            List[str]: List of backup codes
        """
        # Generate random backup codes
        codes = [secrets.token_hex(4) for _ in range(count)]

        # Store codes
        await self.redis.set(f"2fa_backup:{user_id}", ",".join(codes))

        return codes

    async def verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume a backup code.

        Args:
            user_id: User ID
            code: Backup code

        Returns:
            bool: True if verified
        """
        # Check if code exists
        key = f"2fa_backup:{user_id}"
        stored_codes = await self.redis.get(key)
        if stored_codes:
            codes = stored_codes.split(",")
            if code in codes:
                # Remove used code
                codes.remove(code)
                if codes:
                    await self.redis.set(key, ",".join(codes))
                else:
                    await self.redis.delete(key)
                return True
        return False


# Global instance
two_factor_auth = TwoFactorAuth()
