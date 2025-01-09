"""FastAPI application module."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, Optional
from uuid import UUID

from fastapi import FastAPI
from pydantic import BaseModel
from prometheus_fastapi_instrumentator import Instrumentator

from api.routers import api_router
from api.security.middleware import AuditMiddleware
from core.config.settings import settings
from core.exceptions.handlers import setup_error_handlers
from database.management import run_migrations


# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    filename=settings.LOG_FILE,
)

logger = logging.getLogger(__name__)


class RootResponse(BaseModel):
    """Root response model."""

    name: str = settings.PROJECT_NAME
    version: str = settings.VERSION


class BacktestRequest(BaseModel):
    """Custom request class with user info."""

    user_id: Optional[UUID] = None
    is_authenticated: bool = False


class BacktestResponse(BaseModel):
    """Custom response class with metadata."""

    data: Any
    metadata: Optional[Dict[str, Any]] = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan events.

    Args:
        app: FastAPI application instance
    """
    logger.info("Starting application")
    try:
        # Run database migrations on startup
        await run_migrations()
        logger.info("Database migrations completed")

        # Initialize Prometheus metrics
        Instrumentator().instrument(app).expose(app)
        logger.info("Prometheus metrics initialized")

        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        raise
    finally:
        logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create FastAPI application.

    Returns:
        FastAPI: Application instance
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description="BackTest AI API",
        docs_url="/docs" if settings.ENABLE_DOCS else None,
        redoc_url="/redoc" if settings.ENABLE_DOCS else None,
        lifespan=lifespan,
    )

    # Add middleware
    app.add_middleware(AuditMiddleware)

    # Set up error handlers
    setup_error_handlers(app)

    # Add routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", response_model=RootResponse)
    async def root() -> Dict[str, Any]:
        """Root endpoint.

        Returns:
            Dict[str, Any]: Root response
        """
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
        }

    return app


# Create application instance
app = create_app()
