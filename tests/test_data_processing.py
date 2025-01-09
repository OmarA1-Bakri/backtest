"""Test data processing functionality."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import os
from pathlib import Path

from data_processing import (
    load_data,
    add_technical_indicators,
    add_technical_indicators_original,
    preprocess_data,
)


@pytest.fixture
def mock_config(monkeypatch, tmp_path):
    """Create a mock config with data_dir."""

    class MockConfig:
        data_dir = str(tmp_path)

    monkeypatch.setattr("data_processing.config", MockConfig())


@pytest.fixture
def sample_data_file(tmp_path):
    """Create a sample CSV file with test data."""
    df = pd.DataFrame(
        {
            "Date": pd.date_range(start="2023-01-01", periods=100),
            "Open": np.random.uniform(100, 200, 100),
            "High": np.random.uniform(150, 250, 100),
            "Low": np.random.uniform(50, 150, 100),
            "Close": np.random.uniform(100, 200, 100),
            "Volume": np.random.uniform(1000000, 5000000, 100),
        }
    )
    file_path = tmp_path / "test_data.csv"
    df.to_csv(file_path, index=False)
    return str(file_path)


@pytest.fixture
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame(
        {
            "Date": pd.date_range(start="2023-01-01", periods=100),
            "Open": np.random.uniform(100, 200, 100),
            "High": np.random.uniform(150, 250, 100),
            "Low": np.random.uniform(50, 150, 100),
            "Close": np.random.uniform(100, 200, 100),
            "Volume": np.random.uniform(1000000, 5000000, 100),
        }
    ).set_index("Date")


def test_load_data(sample_data_file):
    """Test loading data from CSV file."""
    # Test successful load
    df = load_data(sample_data_file)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert df.index.name == "Date"
    assert all(col in df.columns for col in ["Open", "High", "Low", "Close", "Volume"])

    # Test loading non-existent file
    with pytest.raises(Exception):
        load_data("non_existent_file.csv")

    # Test loading invalid CSV
    invalid_file = Path(sample_data_file).parent / "invalid.csv"
    invalid_file.write_text("invalid,csv,content")
    with pytest.raises(Exception):
        load_data(str(invalid_file))


def test_add_technical_indicators(sample_dataframe):
    """Test adding technical indicators."""
    # Test successful indicator addition
    df = add_technical_indicators(sample_dataframe)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty

    # Check if all indicators are present
    expected_indicators = ["SMA20", "EMA20", "RSI", "BB_upper", "BB_middle", "BB_lower"]
    assert all(indicator in df.columns for indicator in expected_indicators)

    # Check if indicators have correct values
    assert not df["SMA20"].isna().all()
    assert not df["EMA20"].isna().all()
    assert not df["RSI"].isna().all()
    assert not df["BB_upper"].isna().all()

    # Test with invalid dataframe
    invalid_df = pd.DataFrame({"Invalid": [1, 2, 3]})
    with pytest.raises(Exception):
        add_technical_indicators(invalid_df)


def test_add_technical_indicators_original(sample_dataframe, mock_config, monkeypatch):
    """Test adding technical indicators using original method."""

    # Mock MarketDataService
    class MockMarketDataService:
        def __init__(self, data_dir):
            pass

        def _add_technical_indicators(self, df):
            df["SMA"] = df["Close"].rolling(window=20).mean()
            return df

    monkeypatch.setattr("data_processing.MarketDataService", MockMarketDataService)

    # Test successful indicator addition
    df = add_technical_indicators_original(sample_dataframe)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "SMA" in df.columns
    assert not df["SMA"].isna().all()

    # Test with invalid dataframe
    invalid_df = pd.DataFrame({"Invalid": [1, 2, 3]})
    with pytest.raises(Exception):
        add_technical_indicators_original(invalid_df)


def test_preprocess_data(sample_dataframe):
    """Test data preprocessing."""
    features = ["Close", "Volume"]
    target = "Close"

    # Test with valid inputs
    result = preprocess_data(sample_dataframe, features, target)
    assert isinstance(result, dict)
    assert "X" in result
    assert "X_seq" in result
    assert "y" in result
    assert result["X"].shape[1] == len(features)
    assert len(result["y"]) == len(sample_dataframe) - 20  # Due to lookback

    # Test without target
    result = preprocess_data(sample_dataframe, features)
    assert "y" not in result
    assert "X" in result
    assert "X_seq" in result

    # Test with custom lookback
    result = preprocess_data(sample_dataframe, features, target, lookback=10)
    assert len(result["y"]) == len(sample_dataframe) - 10

    # Test with invalid features
    with pytest.raises(Exception):
        preprocess_data(sample_dataframe, ["InvalidFeature"])

    # Test with invalid target
    result = preprocess_data(sample_dataframe, features, "InvalidTarget")
    assert "y" not in result  # Should skip target if not found in columns


def test_data_preprocessing_edge_cases(sample_dataframe):
    """Test edge cases in data preprocessing."""
    features = ["Close", "Volume"]

    # Test with lookback larger than data size
    result = preprocess_data(sample_dataframe.iloc[:10], features, lookback=20)
    assert result["X_seq"].size == 0

    # Test with minimum required data
    min_df = sample_dataframe.iloc[:21]  # Just enough for lookback=20
    result = preprocess_data(min_df, features, lookback=20)
    assert result["X_seq"].shape[0] == 2  # Should have 2 sequences

    # Test with NaN values in feature columns
    df_with_nan = sample_dataframe.copy()
    df_with_nan.loc[df_with_nan.index[0], "Close"] = np.nan
    with pytest.raises(Exception):
        preprocess_data(df_with_nan, features)
