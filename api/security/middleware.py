"""Security middleware module."""

import redis.asyncio as redis
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp
from typing import Optional, Callable, Awaitable
from fastapi import status
import logging

from core.config.settings import settings
from api.security.audit import get_audit_logger, log_audit_entry
from core.database.session import get_async_session_context
from core.exceptions.handlers import create_error_response
from core.exceptions.base import ServiceError, BackTestError, RateLimitError

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security middleware for adding security headers."""

    def __init__(self, app: ASGIApp):
        """Initialize middleware."""
        super().__init__(app)
        self.security_headers = {
            "X-Frame-Options": "DENY",
            "X-Content-Type-Options": "nosniff",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline';"
            ),
        }

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        for header_key, header_value in self.security_headers.items():
            response.headers[header_key] = header_value
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware."""

    def __init__(
        self,
        app: ASGIApp,
        redis_client: Optional[redis.Redis] = None,
        rate_limit: int = None,
    ):
        """Initialize middleware."""
        super().__init__(app)
        self.redis = redis_client or redis.from_url(settings.REDIS_URL)
        self.rate_limit = (
            rate_limit or settings.RATE_LIMIT_PER_MINUTE
        )  # requests per minute
        self.window = 60  # seconds

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Rate limit requests."""
        try:
            client_ip = request.client.host
            key = f"rate_limit:{client_ip}"

            # Get current request count
            count = await self.redis.get(key)
            count = int(count) if count else 0

            if count >= self.rate_limit:
                # Get time until reset
                ttl = await self.redis.ttl(key)
                return create_error_response(
                    RateLimitError(
                        message="Too many requests",
                        limit=self.rate_limit,
                        reset_after=ttl,
                        details={
                            "window": self.window,
                            "current_count": count,
                        },
                    ),
                    status.HTTP_429_TOO_MANY_REQUESTS,
                )

            # Increment request count
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, self.window)
            await pipe.execute()

            return await call_next(request)
        except redis.ConnectionError as e:
            logger.error(f"Redis connection error in rate limiter: {e}")
            # If Redis is down, allow the request to proceed
            return await call_next(request)
        except Exception as e:
            logger.error(f"Unexpected error in rate limiter: {e}")
            return create_error_response(
                ServiceError(
                    message="Rate limiting service error",
                    details={"error": str(e)},
                ),
                status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AuditMiddleware(BaseHTTPMiddleware):
    """Audit middleware."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and log to audit log.

        Args:
            request: FastAPI request
            call_next: Next middleware in chain

        Returns:
            Response: FastAPI response
        """
        # Get database session
        async with get_async_session_context() as session:
            try:
                # Process request
                response = await call_next(request)

                # Log successful request
                await log_audit_entry(
                    request=request,
                    session=session,
                    event_type="request",
                    status="success",
                    details={
                        "status_code": response.status_code,
                        "path": str(request.url),
                        "method": request.method,
                    },
                )

                return response

            except Exception as e:
                # Log failed request
                await log_audit_entry(
                    request=request,
                    session=session,
                    event_type="request",
                    status="error",
                    error_message=str(e),
                    details={
                        "path": str(request.url),
                        "method": request.method,
                        "error": str(e),
                    },
                )
                raise
