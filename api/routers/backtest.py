"""Backtest router."""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.settings import settings
from core.security.auth_consolidated import get_current_user
from api.deps import get_session
from database.models.user import User
from database.models.backtest import Backtest
from api.schemas.backtest import BacktestCreate, BacktestRead

router = APIRouter()


@router.post("/", response_model=BacktestRead)
async def create_backtest(
    backtest_in: BacktestCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Create a new backtest."""
    # Create backtest
    backtest = Backtest(
        name=backtest_in.name,
        description=backtest_in.description,
        user_id=current_user.id,
    )
    session.add(backtest)
    await session.commit()
    await session.refresh(backtest)

    return backtest


@router.get("/", response_model=List[BacktestRead])
async def list_backtests(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """List backtests endpoint."""
    backtests = (
        session.query(Backtest)
        .filter(Backtest.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return backtests


@router.get("/{backtest_id}", response_model=BacktestRead)
async def read_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Get backtest by ID."""
    # Get backtest
    backtest = await session.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found",
        )

    # Check if user owns backtest
    if backtest.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges",
        )

    return backtest


@router.delete("/{backtest_id}")
async def delete_backtest(
    backtest_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete backtest endpoint."""
    backtest = await session.get(Backtest, backtest_id)
    if not backtest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Backtest not found",
        )
    if backtest.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough privileges",
        )
    await session.delete(backtest)
    await session.commit()
    return {"ok": True}
