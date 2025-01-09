"""Tests for password policy enforcement."""

import pytest

from core.security.password_policy import PasswordPolicy


def test_password_validation():
    """Test password validation against policy."""
    policy = PasswordPolicy(
        min_length=12,
        require_uppercase=True,
        require_lowercase=True,
        require_numbers=True,
        require_special=True,
        max_length=128,
        min_strength=3,
    )

    # Test valid password
    valid_password = "SecureP@ssw0rd123"
    is_valid, errors = policy.validate_password(valid_password)
    assert is_valid
    assert len(errors) == 0

    # Test too short password
    short_password = "Short1@"
    is_valid, errors = policy.validate_password(short_password)
    assert not is_valid
    assert any("length" in error.lower() for error in errors)

    # Test missing uppercase
    no_upper = "securepassw0rd@"
    is_valid, errors = policy.validate_password(no_upper)
    assert not is_valid
    assert any("uppercase" in error.lower() for error in errors)

    # Test missing lowercase
    no_lower = "SECUREPASSW0RD@"
    is_valid, errors = policy.validate_password(no_lower)
    assert not is_valid
    assert any("lowercase" in error.lower() for error in errors)

    # Test missing number
    no_number = "SecurePassword@"
    is_valid, errors = policy.validate_password(no_number)
    assert not is_valid
    assert any("number" in error.lower() for error in errors)

    # Test missing special character
    no_special = "SecurePassword123"
    is_valid, errors = policy.validate_password(no_special)
    assert not is_valid
    assert any("special" in error.lower() for error in errors)


def test_password_strength():
    """Test password strength checking."""
    policy = PasswordPolicy(min_strength=3)

    # Test weak password
    weak_password = "password123!"
    is_valid, errors = policy.validate_password(weak_password)
    assert not is_valid
    assert any("weak" in error.lower() for error in errors)

    # Test strong password
    strong_password = "c0rr3ct_h0rs3_b@tt3ry_st@pl3"
    is_valid, errors = policy.validate_password(strong_password)
    assert is_valid
    assert len(errors) == 0


def test_password_generation():
    """Test password generation."""
    policy = PasswordPolicy()

    # Generate multiple passwords
    for _ in range(5):
        password = policy.generate_password()
        is_valid, errors = policy.validate_password(password)
        assert is_valid
        assert len(errors) == 0


def test_user_input_validation():
    """Test password validation against user inputs."""
    policy = PasswordPolicy()

    # Test password containing username
    user_inputs = ["testuser", "test@example.com"]
    password = "TestUser123!@#"
    is_valid, errors = policy.validate_password(password, user_inputs)
    assert not is_valid
    assert len(errors) > 0  # Should warn about using username in password
