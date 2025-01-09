import logging
import json
import uuid
import traceback
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger
from flask import request, has_request_context
from core.config.settings import config


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

        # Add request context if available
        if has_request_context():
            log_record["request_id"] = getattr(request, "request_id", str(uuid.uuid4()))
            log_record["method"] = request.method
            log_record["path"] = request.path
            log_record["ip"] = request.remote_addr

        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "stacktrace": traceback.format_exception(*record.exc_info),
            }

        # Add custom fields
        log_record["environment"] = config.get("ENVIRONMENT", "development")
        log_record["service"] = "backtest-api"


def setup_logging():
    """Configure structured logging for the application."""
    # Create logger
    logger = logging.getLogger("backtest")
    logger.setLevel(logging.INFO)

    # Create console handler with custom JSON formatter
    console_handler = logging.StreamHandler()
    formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler for persistent logging
    file_handler = logging.FileHandler("logs/backtest.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Optionally add Sentry handler if configured
    if config.get("SENTRY_DSN"):
        import sentry_sdk
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_logging = LoggingIntegration(
            level=logging.INFO, event_level=logging.ERROR
        )

        sentry_sdk.init(
            dsn=config.get("SENTRY_DSN"),
            environment=config.get("ENVIRONMENT", "development"),
            traces_sample_rate=1.0,
            integrations=[sentry_logging],
        )

    return logger


# Create and configure logger
logger = setup_logging()
