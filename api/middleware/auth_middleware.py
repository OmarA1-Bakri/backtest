from functools import wraps
from flask import request, g
from core.security.auth import verify_token, get_token_from_header
from core.exceptions import AuthenticationError
from models.user import User
from sqlalchemy.orm import Session
from database import get_db


def get_current_user():
    """Get current authenticated user from database."""
    if not hasattr(g, "current_user"):
        raise AuthenticationError("User not authenticated")
    return g.current_user


def require_auth(f):
    """Decorator to require authentication for routes."""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            auth_header = request.headers.get("Authorization")
            token = get_token_from_header(auth_header)
            payload = verify_token(token)

            # Get user from database
            db: Session = next(get_db())
            user = db.query(User).filter(User.id == payload["sub"]).first()
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            # Store user in request context
            g.current_user = user
            return f(*args, **kwargs)

        except AuthenticationError as e:
            return {"error": str(e)}, 401
        except Exception as e:
            return {"error": "Internal server error"}, 500

    return decorated


def require_superuser(f):
    """Decorator to require superuser privileges."""

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            user = get_current_user()
            if not user.is_superuser:
                return {"error": "Superuser privileges required"}, 403
            return f(*args, **kwargs)
        except AuthenticationError as e:
            return {"error": str(e)}, 401
        except Exception as e:
            return {"error": "Internal server error"}, 500

    return decorated
