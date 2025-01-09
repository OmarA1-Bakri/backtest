"""Audit service module."""

from datetime import datetime
from typing import Any, Dict, Optional, List
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.audit import AuditLog


async def create_audit_log(
    session: AsyncSession,
    event_type: str,
    user_id: UUID = None,
    details: Dict[str, Any] = None,
    status: str = "success",
    error_message: str = None,
    request_method: str = None,
    request_url: str = None,
    request_headers: Dict[str, str] = None,
    request_ip: str = None,
    request_user_agent: str = None,
    timestamp: datetime = None,
) -> AuditLog:
    """Create audit log entry.

    Args:
        session: Database session
        event_type: Type of event
        user_id: ID of user who triggered event
        details: Additional details about event
        status: Status of event
        error_message: Error message if event failed
        request_method: HTTP method of request
        request_url: URL of request
        request_headers: Headers of request
        request_ip: IP address of request
        request_user_agent: User agent of request
        timestamp: Timestamp of event

    Returns:
        AuditLog: Created audit log entry
    """
    audit_log = AuditLog(
        id=uuid4(),
        timestamp=timestamp or datetime.utcnow(),
        event_type=event_type,
        user_id=user_id,
        details=details,
        status=status,
        error_message=error_message,
        request_method=request_method,
        request_url=request_url,
        request_headers=request_headers,
        request_ip=request_ip,
        request_user_agent=request_user_agent,
    )
    session.add(audit_log)
    await session.flush()
    return audit_log


async def get_audit_logs(
    session: AsyncSession,
    user_id: Optional[UUID] = None,
    event_type: Optional[str] = None,
    status: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[AuditLog]:
    """Get audit logs with optional filters.

    Args:
        session: Database session
        user_id: Filter by user ID
        event_type: Filter by event type
        status: Filter by status
        start_time: Filter by start time
        end_time: Filter by end time
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List[AuditLog]: List of audit logs
    """
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if status:
        query = query.filter(AuditLog.status == status)
    if start_time:
        query = query.filter(AuditLog.timestamp >= start_time)
    if end_time:
        query = query.filter(AuditLog.timestamp <= end_time)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_audit_log(
    session: AsyncSession, audit_log_id: UUID
) -> Optional[AuditLog]:
    """Get audit log by ID.

    Args:
        session: Database session
        audit_log_id: ID of audit log to get

    Returns:
        Optional[AuditLog]: Audit log if found, None otherwise
    """
    query = select(AuditLog).filter(AuditLog.id == audit_log_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def delete_audit_logs(session: AsyncSession, before_time: datetime) -> int:
    """Delete audit logs before specified time.

    Args:
        session: Database session
        before_time: Delete logs before this time

    Returns:
        int: Number of logs deleted
    """
    query = select(AuditLog).filter(AuditLog.timestamp < before_time)
    result = await session.execute(query)
    logs = result.scalars().all()

    for log in logs:
        await session.delete(log)

    await session.flush()
    return len(logs)
