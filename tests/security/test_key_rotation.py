import pytest
from datetime import datetime, timedelta
from api.security.key_rotation import APIKeyRotator, APIKey


def test_generate_new_key():
    rotator = APIKeyRotator(rotation_interval_hours=24)
    api_key = rotator.generate_new_key()

    assert isinstance(api_key, APIKey)
    assert len(api_key.key) > 0
    assert api_key.is_active
    assert api_key.expires_at > api_key.created_at
    assert api_key.expires_at - api_key.created_at == timedelta(hours=24)


def test_key_rotation_deactivates_old_key():
    rotator = APIKeyRotator(rotation_interval_hours=24)
    first_key = rotator.generate_new_key()
    second_key = rotator.generate_new_key()

    assert not first_key.is_active
    assert second_key.is_active
    assert not rotator.validate_key(first_key.key)
    assert rotator.validate_key(second_key.key)


def test_validate_key():
    rotator = APIKeyRotator(rotation_interval_hours=24)
    api_key = rotator.generate_new_key()

    assert rotator.validate_key(api_key.key)
    assert not rotator.validate_key("invalid-key")


def test_cleanup_expired_keys():
    rotator = APIKeyRotator(rotation_interval_hours=1)
    api_key = rotator.generate_new_key()

    # Manually expire the key
    api_key.expires_at = datetime.utcnow() - timedelta(hours=1)
    rotator._keys[api_key.key] = api_key

    rotator.cleanup_expired_keys()
    assert api_key.key not in rotator._keys
