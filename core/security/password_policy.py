"""Password policy enforcement."""

import re
from typing import List, Tuple

from passlib.pwd import genword
from zxcvbn import zxcvbn


class PasswordPolicy:
    """Password policy enforcement."""

    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_numbers: bool = True,
        require_special: bool = True,
        max_length: int = 128,
        min_strength: int = 3,
    ):
        """Initialize password policy.

        Args:
            min_length: Minimum password length
            require_uppercase: Require uppercase letters
            require_lowercase: Require lowercase letters
            require_numbers: Require numbers
            require_special: Require special characters
            max_length: Maximum password length
            min_strength: Minimum zxcvbn strength score (0-4)
        """
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_numbers = require_numbers
        self.require_special = require_special
        self.max_length = max_length
        self.min_strength = min_strength

    def validate_password(
        self, password: str, user_inputs: List[str] = None
    ) -> Tuple[bool, List[str]]:
        """Validate password against policy.

        Args:
            password: Password to validate
            user_inputs: List of user-specific strings to check against

        Returns:
            Tuple[bool, List[str]]: (is_valid, list of validation errors)
        """
        errors = []

        # Check length
        if len(password) < self.min_length:
            errors.append(
                f"Password must be at least {self.min_length} characters long"
            )
        if len(password) > self.max_length:
            errors.append(f"Password must be at most {self.max_length} characters long")

        # Check character requirements
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        if self.require_numbers and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        if self.require_special and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            errors.append("Password must contain at least one special character")

        # Check password strength using zxcvbn
        user_inputs = user_inputs or []
        strength_result = zxcvbn(password, user_inputs)

        if strength_result["score"] < self.min_strength:
            suggestions = strength_result.get("feedback", {}).get("suggestions", [])
            errors.extend(suggestions)
            errors.append(f"Password is too weak (score: {strength_result['score']}/4)")

        return len(errors) == 0, errors

    def generate_password(self) -> str:
        """Generate a password that meets the policy requirements.

        Returns:
            str: Generated password
        """
        while True:
            # Generate base password
            password = genword(length=self.min_length)

            # Add required character types if missing
            if self.require_uppercase and not re.search(r"[A-Z]", password):
                password += "A"
            if self.require_lowercase and not re.search(r"[a-z]", password):
                password += "a"
            if self.require_numbers and not re.search(r"\d", password):
                password += "1"
            if self.require_special and not re.search(
                r"[!@#$%^&*(),.?\":{}|<>]", password
            ):
                password += "!"

            # Validate the generated password
            is_valid, _ = self.validate_password(password)
            if is_valid:
                return password


# Global instance with default settings
password_policy = PasswordPolicy()
