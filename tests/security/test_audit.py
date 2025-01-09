"""Test module for audit logging functionality."""

import pytest
import json
import logging
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from api.security.audit import AuditLogger, audit_log
from database.models.audit import AuditLog
from database.models.user import User


@pytest.fixture
def app():
    """Create test FastAPI app."""
    app = FastAPI()
    return app


@pytest.fixture
def test_user(db_session):
    """Create a test user."""
    user = User(
        email="test@example.com", hashed_password="hashedpassword", is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def audit_logger(db_session):
    """Create test audit logger."""
    logger = AuditLogger(db_session=db_session)
    return logger


def test_audit_log_event(audit_logger, db_session):
    """Test basic audit logging."""
    # Log test event
    audit_logger.log_event(
        event_type="test_event",
        message="Test audit message",
        user_id="test_user",
        details={"key": "value"},
    )

    # Check database log
    db_log = db_session.query(AuditLog).first()
    assert db_log is not None
    assert db_log.action == "test_event"
    assert db_log.user_id == "test_user"
    assert db_log.details == {"key": "value"}


def test_audit_log_decorator(app, audit_logger, tmp_path, db_session):
    """Test audit log decorator."""

    @app.get("/test")
    @audit_log("test_operation")
    async def test_endpoint(request: Request):
        return {"status": "success"}

    client = TestClient(app)
    response = client.get("/test")
    assert response.status_code == 200

    # Check database log
    db_log = db_session.query(AuditLog).first()
    assert db_log is not None
    assert db_log.action == "test_operation"
    assert db_log.resource_type == "endpoint"
    assert db_log.details.get("path") == "/test"
    assert db_log.details.get("method") == "GET"


def test_audit_log_decorator_exception(app, audit_logger, tmp_path, db_session):
    """Test audit log decorator with exception."""

    @app.get("/error")
    @audit_log("error_operation")
    async def error_endpoint(request: Request):
        raise ValueError("Test error")

    client = TestClient(app)
    with pytest.raises(ValueError):
        response = client.get("/error")

    # Check database log
    db_log = db_session.query(AuditLog).first()
    assert db_log is not None
    assert db_log.action == "error_operation"
    assert db_log.details.get("error") == "Test error"
    assert db_log.details.get("status") == "error"


def test_audit_log_with_user(app, audit_logger, tmp_path, db_session, test_user):
    """Test audit logging with authenticated user."""

    @app.get("/user-test")
    @audit_log("user_operation")
    async def user_endpoint(request: Request):
        request.state.user = test_user
        return {"status": "success"}

    client = TestClient(app)
    response = client.get("/user-test")
    assert response.status_code == 200

    # Check database log
    db_log = db_session.query(AuditLog).first()
    assert db_log is not None
    assert db_log.user_id == str(test_user.id)
    assert db_log.action == "user_operation"
