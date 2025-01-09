"""Strategy router."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.session import get_async_session
from database.models.user import User
from database.models.strategy import Strategy
from schemas.strategy import StrategyCreate, StrategyResponse
from core.security.auth import get_current_user

router = APIRouter()


@router.post("/", response_model=StrategyResponse)
async def create_strategy(
    strategy: StrategyCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Create strategy endpoint."""
    db_strategy = Strategy(**strategy.dict(), user_id=current_user.id)
    session.add(db_strategy)
    await session.commit()
    await session.refresh(db_strategy)
    return db_strategy


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """List strategies endpoint."""
    strategies = (
        session.query(Strategy)
        .filter(Strategy.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Get strategy endpoint."""
    strategy = (
        session.query(Strategy)
        .filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )
    return strategy


@router.delete("/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Delete strategy endpoint."""
    strategy = (
        session.query(Strategy)
        .filter(Strategy.id == strategy_id, Strategy.user_id == current_user.id)
        .first()
    )
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Strategy not found",
        )
    await session.delete(strategy)
    await session.commit()
    return {"ok": True}
