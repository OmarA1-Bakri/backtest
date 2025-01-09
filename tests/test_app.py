"""Test module for FastAPI application."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from api.app import app, BacktestRequest, BacktestResponse
from core.security.auth import create_access_token
from core.config.settings import settings


@pytest.fixture
def test_token():
    """Create a test token."""
    access_token = create_access_token(
        data={"sub": "testuser"}, expires_delta=timedelta(minutes=30)
    )
    return access_token


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient):
    """Test health check endpoint."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == settings.APP_NAME


@pytest.mark.asyncio
async def test_backtest_endpoint(test_client: AsyncClient, test_token: str, db_session):
    """Test backtest endpoint."""
    headers = {"Authorization": f"Bearer {test_token}"}
    request_data = {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100000.0,
        "strategy_params": {"short_window": 20, "long_window": 50},
        "risk_params": {"stop_loss": 0.02, "take_profit": 0.05},
        "data_source": "yahoo",
        "data_source_params": {"symbol": "AAPL"},
    }

    # Mock the market data fetching
    mock_data = pd.DataFrame(
        {
            "Open": [100] * 10,
            "High": [105] * 10,
            "Low": [95] * 10,
            "Close": [102] * 10,
            "Volume": [1000000] * 10,
        },
        index=pd.date_range("2023-01-01", periods=10),
    )

    with patch(
        "data.sources.yahoo_source.YahooDataSource.get_data", return_value=mock_data
    ):
        response = await test_client.post(
            "/api/v1/backtest/run", headers=headers, json=request_data
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "returns" in data
        assert "metrics" in data
        assert "positions" in data
        assert "risk_metrics" in data


@pytest.mark.asyncio
async def test_backtest_invalid_dates(test_client: AsyncClient, test_token: str):
    """Test backtest endpoint with invalid dates."""
    headers = {"Authorization": f"Bearer {test_token}"}
    request_data = {
        "start_date": "2023-13-01",  # Invalid date
        "end_date": "2023-12-31",
        "initial_capital": 100000.0,
        "strategy_params": {},
    }

    response = await test_client.post(
        "/api/v1/backtest/run", headers=headers, json=request_data
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_backtest_unauthorized(test_client: AsyncClient):
    """Test backtest endpoint without token."""
    request_data = {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100000.0,
        "strategy_params": {},
    }

    response = await test_client.post("/api/v1/backtest/run", json=request_data)

    assert response.status_code == 401  # Unauthorized
