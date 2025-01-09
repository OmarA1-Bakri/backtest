"""Health check endpoint."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.config.settings import settings


router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    name: str = settings.PROJECT_NAME
    version: str = settings.VERSION
    status: str = "healthy"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        HealthResponse: Health check response
    """
    return HealthResponse()
