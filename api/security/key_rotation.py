from datetime import datetime, timedelta
import secrets
from typing import Dict, Optional
import threading
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    key: str
    created_at: datetime
    expires_at: datetime
    is_active: bool = True


class APIKeyRotator:
    def __init__(self, rotation_interval_hours: int = 24):
        self._keys: Dict[str, APIKey] = {}
        self._rotation_interval = timedelta(hours=rotation_interval_hours)
        self._lock = threading.Lock()
        self._current_key: Optional[APIKey] = None

    def generate_new_key(self) -> APIKey:
        """Generate a new API key with expiration"""
        with self._lock:
            new_key = secrets.token_urlsafe(32)
            created_at = datetime.utcnow()
            expires_at = created_at + self._rotation_interval
            api_key = APIKey(key=new_key, created_at=created_at, expires_at=expires_at)

            # Deactivate current key after grace period
            if self._current_key:
                self._current_key.is_active = False
                self._keys[self._current_key.key] = self._current_key

            self._current_key = api_key
            self._keys[new_key] = api_key

            logger.info(
                "Generated new API key",
                extra={
                    "created_at": created_at.isoformat(),
                    "expires_at": expires_at.isoformat(),
                },
            )
            return api_key

    def validate_key(self, key: str) -> bool:
        """Validate if an API key is active and not expired"""
        api_key = self._keys.get(key)
        if not api_key:
            return False

        now = datetime.utcnow()
        return api_key.is_active and now < api_key.expires_at

    def get_current_key(self) -> Optional[APIKey]:
        """Get the currently active API key"""
        return self._current_key

    def cleanup_expired_keys(self) -> None:
        """Remove expired keys from storage"""
        with self._lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, api_key in self._keys.items() if now > api_key.expires_at
            ]
            for key in expired_keys:
                del self._keys[key]
                logger.info(f"Removed expired API key", extra={"key_id": key[:8]})
