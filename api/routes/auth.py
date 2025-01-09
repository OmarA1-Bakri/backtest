from datetime import datetime
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import Session
from core.security.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from core.exceptions import AuthenticationError
from models.user import User, UserCreate, UserLogin, Token
from database import get_db
from api.middleware.auth_middleware import require_auth

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register a new user."""
    try:
        data = UserCreate(**request.json)
        db: Session = next(get_db())

        # Check if user exists
        if db.query(User).filter(User.email == data.email).first():
            return jsonify({"error": "Email already registered"}), 400
        if db.query(User).filter(User.username == data.username).first():
            return jsonify({"error": "Username already taken"}), 400

        # Create new user
        user = User(
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return jsonify({"message": "User created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return tokens."""
    try:
        data = UserLogin(**request.json)
        db: Session = next(get_db())

        # Find user
        user = db.query(User).filter(User.email == data.email).first()
        if not user or not verify_password(data.password, user.hashed_password):
            return jsonify({"error": "Invalid credentials"}), 401

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Generate tokens
        access_token = create_access_token({"sub": user.id})
        refresh_token = create_refresh_token({"sub": user.id})

        return jsonify(
            Token(access_token=access_token, refresh_token=refresh_token).dict()
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/refresh", methods=["POST"])
def refresh_token():
    """Refresh access token using refresh token."""
    try:
        refresh_token = request.json.get("refresh_token")
        if not refresh_token:
            return jsonify({"error": "Refresh token required"}), 400

        # Verify refresh token
        payload = verify_token(refresh_token, token_type="refresh")

        # Generate new access token
        access_token = create_access_token({"sub": payload["sub"]})

        return jsonify({"access_token": access_token})

    except AuthenticationError as e:
        return jsonify({"error": str(e)}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/me", methods=["GET"])
@require_auth
def get_current_user():
    """Get current user information."""
    try:
        from flask import g

        return jsonify(g.current_user), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
