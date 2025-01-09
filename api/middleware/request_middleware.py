import time
import uuid
from functools import wraps
from flask import request, g
from prometheus_client import Counter, Histogram
from core.logging_config import logger

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency", ["method", "endpoint"]
)

ERROR_COUNT = Counter(
    "http_errors_total", "Total HTTP errors", ["method", "endpoint", "error_type"]
)


def request_middleware():
    """Middleware to log requests and collect metrics."""

    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Generate request ID
            request_id = str(uuid.uuid4())
            g.request_id = request_id

            # Start timer
            start_time = time.time()

            # Log request
            logger.info(
                "Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.path,
                    "ip": request.remote_addr,
                    "user_agent": request.user_agent.string,
                },
            )

            try:
                # Execute request
                response = f(*args, **kwargs)

                # Record metrics
                REQUEST_COUNT.labels(
                    method=request.method,
                    endpoint=request.path,
                    status=response.status_code,
                ).inc()

                REQUEST_LATENCY.labels(
                    method=request.method, endpoint=request.path
                ).observe(time.time() - start_time)

                # Log response
                logger.info(
                    "Request completed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.path,
                        "status_code": response.status_code,
                        "duration": time.time() - start_time,
                    },
                )

                return response

            except Exception as e:
                # Record error metrics
                ERROR_COUNT.labels(
                    method=request.method,
                    endpoint=request.path,
                    error_type=type(e).__name__,
                ).inc()

                # Log error
                logger.error(
                    "Request failed",
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.path,
                        "error": str(e),
                        "duration": time.time() - start_time,
                    },
                    exc_info=True,
                )

                raise

        return wrapped

    return decorator
