"""Metrics router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.security.auth import get_current_user
from database.config import get_db
from database.models.user import User
from database.models.metrics import Metrics
from schemas.metrics import MetricsCreate, MetricsResponse

router = APIRouter()


@router.post("/", response_model=MetricsResponse)
async def create_metrics(
    metrics: MetricsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create metrics endpoint."""
    db_metrics = Metrics(**metrics.dict(), user_id=current_user.id)
    db.add(db_metrics)
    db.commit()
    db.refresh(db_metrics)
    return db_metrics


@router.get("/", response_model=List[MetricsResponse])
async def list_metrics(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List metrics endpoint."""
    metrics = (
        db.query(Metrics)
        .filter(Metrics.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return metrics


@router.get("/{metrics_id}", response_model=MetricsResponse)
async def get_metrics(
    metrics_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get metrics endpoint."""
    metrics = (
        db.query(Metrics)
        .filter(Metrics.id == metrics_id, Metrics.user_id == current_user.id)
        .first()
    )
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics not found",
        )
    return metrics


@router.delete("/{metrics_id}")
async def delete_metrics(
    metrics_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete metrics endpoint."""
    metrics = (
        db.query(Metrics)
        .filter(Metrics.id == metrics_id, Metrics.user_id == current_user.id)
        .first()
    )
    if not metrics:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metrics not found",
        )
    db.delete(metrics)
    db.commit()
    return {"ok": True}
