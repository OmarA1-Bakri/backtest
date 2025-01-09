"""Audit logging module."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import get_async_session
from core.models.audit import AuditLog
from core.services.audit import create_audit_log

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logger class."""

    def __init__(self, db: AsyncSession):
        """Initialize audit logger.

        Args:
            db: Database session
        """
        self.db = db

    async def log_request(
        self,
        request: Request,
        response: Response,
        user_id: Optional[UUID] = None,
        error_detail: Optional[str] = None,
    ) -> None:
        """Log request to audit log.

        Args:
            request: FastAPI request
            response: FastAPI response
            user_id: User ID
            error_detail: Error detail
        """
        try:
            # Create audit log entry
            audit_log = AuditLog(
                created_at=datetime.utcnow(),
                user_id=user_id,
                method=request.method,
                path=str(request.url),
                status_code=response.status_code,
                request_body=(
                    json.dumps(await request.json())
                    if request.method in ["POST", "PUT", "PATCH"]
                    else None
                ),
                error_detail=error_detail,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                action="request",  # Add default action for requests
            )

            # Add to session and commit
            self.db.add(audit_log)
            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log request: {str(e)}")


async def get_audit_logger(
    request: Request, session: AsyncSession = None
) -> AsyncSession:
    """Get audit logger."""
    if not session:
        session = await anext(get_async_session())
    return session


def audit_log(
    event_type: str,
    operation: Optional[str] = None,
    include_request_details: bool = True,
):
    """Decorator to log audit events.

    Args:
        event_type: Type of event to log
        operation: Optional operation name for performance monitoring
        include_request_details: Whether to include request details in log
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request and session from kwargs
            request = kwargs.get("request")
            session = kwargs.get("session")

            # Extract request details if available
            request_details = {}
            if include_request_details and isinstance(request, Request):
                request_details = {
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "client": request.client.host if request.client else None,
                    "user_agent": request.headers.get("user-agent"),
                }

            try:
                # Execute function
                result = await func(*args, **kwargs)

                # Log successful execution
                if session:
                    await create_audit_log(
                        session=session,
                        event_type=event_type,
                        status="success",
                        details={"request": request_details, "result": str(result)},
                    )

                return result

            except Exception as e:
                # Log error
                if session:
                    await create_audit_log(
                        session=session,
                        event_type=event_type,
                        status="error",
                        error_message=str(e),
                        details={"request": request_details, "error": str(e)},
                    )
                raise

        return wrapper

    return decorator


async def log_audit_entry(
    request: Request,
    session: AsyncSession,
    event_type: str,
    user_id: UUID = None,
    details: Dict[str, Any] = None,
    status: str = "success",
    error_message: str = None,
) -> AuditLog:
    """Log audit entry."""
    try:
        audit_log = await create_audit_log(
            session=session,
            event_type=event_type,
            user_id=user_id,
            details=details,
            status=status,
            error_message=error_message,
            request_method=request.method,
            request_url=str(request.url),
            request_headers=dict(request.headers),
            request_ip=request.client.host if request.client else None,
            request_user_agent=request.headers.get("user-agent"),
            timestamp=datetime.utcnow(),
        )
        await session.commit()
        return audit_log
    except Exception as e:
        await session.rollback()
        raise e
