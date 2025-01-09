"""Integration tests for complete trading workflow."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.model_facade import ModelFacade
from strategies.moving_average import SimpleMAStrategy
from risk.manager import RiskManager
from database.models.backtest_result import BacktestResult
from database.models.strategy import Strategy
from database.models.user import User


def create_test_data(days: int = 100) -> pd.DataFrame:
    """Create test price data."""
    dates = pd.date_range(start=datetime(2024, 1, 1), periods=days, freq="D")

    # Create sine wave price data
    t = np.linspace(0, 4 * np.pi, days)
    base_price = 100
    amplitude = 10
    prices = base_price + amplitude * np.sin(t)

    return pd.DataFrame(
        {
            "open": prices,
            "high": prices * 1.02,
            "low": prices * 0.98,
            "close": prices,
            "volume": np.random.randint(1000, 10000, size=days),
        },
        index=dates,
    )


@pytest.fixture
def test_strategy(db_session: Session, test_user: User) -> Strategy:
    """Create a test strategy."""
    strategy = Strategy(
        name="Test MA Strategy",
        description="Moving average test strategy",
        user_id=test_user.id,
        parameters={"short_window": 5, "long_window": 20, "initial_cash": 10000.0},
    )
    db_session.add(strategy)
    db_session.commit()
    db_session.refresh(strategy)
    return strategy


def test_complete_trading_workflow(
    test_client: TestClient,
    db_session: Session,
    test_user: User,
    test_strategy: Strategy,
    auth_headers: dict,
):
    """Test complete trading workflow from data to results."""
    # 1. Create test data
    data = create_test_data(days=100)

    # 2. Initialize model facade
    features = ["open", "high", "low", "close", "volume"]
    model_facade = ModelFacade(features=features)

    # 3. Initialize risk manager
    risk_manager = RiskManager(
        model_facade=model_facade, initial_cash=10000.0, max_position_size=0.2
    )

    # 4. Initialize strategy
    strategy = SimpleMAStrategy(
        data=data, params=test_strategy.parameters, initial_cash=10000.0
    )
    strategy.risk_manager = risk_manager

    # 5. Run backtest
    response = test_client.post(
        f"/api/v1/backtest/run",
        json={
            "strategy_id": str(test_strategy.id),
            "start_date": "2024-01-01",
            "end_date": "2024-04-10",
            "initial_capital": 10000.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()

    # 6. Verify backtest results
    backtest_result = (
        db_session.query(BacktestResult)
        .filter(BacktestResult.strategy_id == test_strategy.id)
        .first()
    )

    assert backtest_result is not None
    assert backtest_result.initial_capital == 10000.0
    assert backtest_result.final_capital != 10000.0  # Should have some P&L
    assert backtest_result.total_return is not None
    assert backtest_result.sharpe_ratio is not None
    assert backtest_result.max_drawdown is not None
    assert backtest_result.trades_data is not None

    # 7. Check metrics
    metrics_response = test_client.get("/metrics", headers=auth_headers)
    assert metrics_response.status_code == 200
    metrics = metrics_response.text

    assert "backtest_returns" in metrics
    assert "backtest_sharpe_ratio" in metrics
    assert "backtest_max_drawdown" in metrics
    assert "backtest_trades_total" in metrics
    assert "backtest_trading_volume" in metrics

    # 8. Check audit logs
    logs_response = test_client.get("/api/v1/audit/logs", headers=auth_headers)
    assert logs_response.status_code == 200
    logs = logs_response.json()

    assert len(logs) > 0
    assert any(log["action"] == "backtest_run" for log in logs)


def test_error_handling(
    test_client: TestClient,
    db_session: Session,
    test_user: User,
    test_strategy: Strategy,
    auth_headers: dict,
):
    """Test error handling in trading workflow."""
    # Test invalid date range
    response = test_client.post(
        f"/api/v1/backtest/run",
        json={
            "strategy_id": str(test_strategy.id),
            "start_date": "2024-04-10",  # End before start
            "end_date": "2024-01-01",
            "initial_capital": 10000.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "date range" in response.json()["detail"].lower()

    # Test insufficient initial capital
    response = test_client.post(
        f"/api/v1/backtest/run",
        json={
            "strategy_id": str(test_strategy.id),
            "start_date": "2024-01-01",
            "end_date": "2024-04-10",
            "initial_capital": 0.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert "capital" in response.json()["detail"].lower()

    # Test invalid strategy ID
    response = test_client.post(
        f"/api/v1/backtest/run",
        json={
            "strategy_id": "00000000-0000-0000-0000-000000000000",
            "start_date": "2024-01-01",
            "end_date": "2024-04-10",
            "initial_capital": 10000.0,
        },
        headers=auth_headers,
    )
    assert response.status_code == 404
    assert "strategy" in response.json()["detail"].lower()


def test_concurrent_backtests(
    test_client: TestClient,
    db_session: Session,
    test_user: User,
    test_strategy: Strategy,
    auth_headers: dict,
):
    """Test running multiple backtests concurrently."""
    import asyncio
    import httpx

    async def run_backtest(client, params):
        async with httpx.AsyncClient() as aclient:
            response = await aclient.post(
                f"{client.base_url}/api/v1/backtest/run",
                json=params,
                headers=auth_headers,
            )
            return response.json()

    # Create multiple backtest parameters
    params_list = [
        {
            "strategy_id": str(test_strategy.id),
            "start_date": "2024-01-01",
            "end_date": "2024-02-01",
            "initial_capital": 10000.0,
        },
        {
            "strategy_id": str(test_strategy.id),
            "start_date": "2024-02-01",
            "end_date": "2024-03-01",
            "initial_capital": 10000.0,
        },
        {
            "strategy_id": str(test_strategy.id),
            "start_date": "2024-03-01",
            "end_date": "2024-04-01",
            "initial_capital": 10000.0,
        },
    ]

    # Run backtests concurrently
    async def run_all():
        tasks = [run_backtest(test_client, params) for params in params_list]
        return await asyncio.gather(*tasks)

    results = asyncio.run(run_all())

    # Verify results
    assert len(results) == len(params_list)
    for result in results:
        assert "backtest_id" in result

    # Check database
    backtest_results = (
        db_session.query(BacktestResult)
        .filter(BacktestResult.strategy_id == test_strategy.id)
        .all()
    )

    assert len(backtest_results) == len(params_list)
    for result in backtest_results:
        assert result.final_capital is not None
        assert result.trades_data is not None
