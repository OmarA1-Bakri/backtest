"""Test model facade functionality."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from models.model_facade import ModelFacade
from core.config.models import MODEL_CONFIGS
from unittest.mock import MagicMock, patch


@pytest.fixture
def test_data():
    """Create test data for models."""
    # Create enough data points for sequence length
    prices = [10, 12, 14, 13, 15, 16, 17, 18, 19, 20] * 5  # 50 data points
    dates = pd.date_range(start="2020-01-01", periods=len(prices), freq="D")
    data = {
        "Open": prices,
        "High": [p + 1 for p in prices],
        "Low": [p - 1 for p in prices],
        "Close": prices,
        "Volume": [100] * len(prices),
    }
    return pd.DataFrame(data, index=dates)


@pytest.fixture
def model_facade(test_data):
    """Create model facade instance."""
    features = ["Open", "High", "Low", "Close", "Volume"]
    model_settings = {
        "time_steps": 5,  # Small sequence length for testing
        "n_components": 3,
        "model_dir": "test_models",
        "lstm": {
            "epochs": 2,
            "batch_size": 8,
            "hidden_units": [10, 10],  # Smaller network for faster testing
            "dense_units": 5,
        },
        "xgboost": {"n_estimators": 10, "max_depth": 2},
    }
    facade = ModelFacade(features=features, model_settings=model_settings)

    # Mock the strategy
    facade.strategy = MagicMock()
    facade.strategy.combinatorial_purged_cross_validation = MagicMock(
        return_value=[([0, 1, 2, 3, 4, 5, 6, 7], [8, 9])]
    )

    return facade


@pytest.fixture(autouse=True)
def cleanup_model_files():
    """Clean up model files after tests."""
    yield
    model_dir = Path("test_models")
    if model_dir.exists():
        shutil.rmtree(model_dir)


def test_model_facade_initialization(model_facade):
    """Test model facade initialization."""
    assert model_facade.features == ["Open", "High", "Low", "Close", "Volume"]
    assert model_facade.time_steps == 5
    assert model_facade.n_components == 3
    assert isinstance(model_facade.model_dir, Path)
    assert model_facade.model_dir.name == "test_models"


def test_model_facade_train_predict(model_facade, test_data):
    """Test model training and prediction."""
    # Prepare data
    X = test_data[model_facade.features].values
    y = np.random.randint(0, 2, size=len(test_data))  # Binary labels

    # Train models
    model_facade.train_models(X, y)

    # Make predictions
    predictions = model_facade.predict_all(test_data)

    # Check predictions
    assert "xgb" in predictions
    assert "lstm" in predictions
    assert "hmm" in predictions
    assert "ensemble" in predictions

    # Check prediction shapes and types
    assert isinstance(predictions["xgb"], (np.ndarray, float))
    assert isinstance(predictions["lstm"], (np.ndarray, float))
    assert isinstance(predictions["hmm"], (str, np.ndarray))
    assert isinstance(predictions["ensemble"], (float, np.ndarray))


def test_model_persistence(model_facade, test_data):
    """Test model saving and loading."""
    # Prepare data
    X = test_data[model_facade.features].values
    y = np.random.randint(0, 2, size=len(test_data))

    # Train and save models
    model_facade.train_models(X, y)
    model_facade.save_all_models()

    # Verify model directory exists
    assert model_facade.model_dir.exists()

    # Load models and make predictions
    model_facade.load_all_models()
    predictions = model_facade.predict_all(test_data)
    assert all(k in predictions for k in ["xgb", "lstm", "hmm", "ensemble"])


def test_cross_validation(model_facade, test_data):
    """Test cross-validation functionality."""
    # Prepare data
    X = test_data[model_facade.features].values
    y = np.random.randint(0, 2, size=len(test_data))

    # Perform cross-validation
    cv_results = model_facade.cross_validate_models(X, y, n_splits=3)

    # Check results
    assert isinstance(cv_results, dict)
    assert all(model in cv_results for model in ["lstm", "hmm", "xgb"])
    assert all(isinstance(scores, list) for scores in cv_results.values())
    assert all(0 <= score <= 1 for scores in cv_results.values() for score in scores)


def test_error_handling(model_facade):
    """Test error handling in model facade."""
    # Test with invalid data
    invalid_data = pd.DataFrame({"Invalid": [1, 2, 3]})

    # Should handle missing features gracefully
    predictions = model_facade.predict_all(invalid_data)
    assert isinstance(predictions, dict)
    assert all(key in predictions for key in ["xgb", "lstm", "hmm", "ensemble"])
    assert all(isinstance(pred, np.ndarray) for pred in predictions.values())


def test_lstm_sequence_handling(model_facade, test_data):
    """Test LSTM model's sequence handling capabilities."""
    # Prepare data with different lengths
    short_data = test_data.iloc[:3]  # Less than sequence length
    exact_data = test_data.iloc[:5]  # Equal to sequence length
    normal_data = test_data.iloc[:10]  # More than sequence length

    # Prepare features and labels
    X_short = short_data[model_facade.features].values
    X_exact = exact_data[model_facade.features].values
    X_normal = normal_data[model_facade.features].values

    y = np.random.randint(0, 2, size=len(test_data))

    # Train on normal data
    model_facade.train_models(X_normal, y[:10])

    # Test predictions on different data lengths
    short_pred = model_facade.predict_all(short_data)
    exact_pred = model_facade.predict_all(exact_data)
    normal_pred = model_facade.predict_all(normal_data)

    # Check predictions
    for preds in [short_pred, exact_pred, normal_pred]:
        assert isinstance(preds["lstm"], np.ndarray)
        assert len(preds["lstm"]) == len(
            preds["xgb"]
        )  # All models should return same length
        assert all(isinstance(p, (np.ndarray, float)) for p in preds.values())


def test_model_facade_prediction_consistency(model_facade, test_data):
    """Test consistency of predictions across different prediction methods."""
    # Prepare data
    X = test_data[model_facade.features].values
    y = np.random.randint(0, 2, size=len(test_data))

    # Train models
    model_facade.train_models(X, y)

    # Get predictions using different methods
    binary_preds = model_facade.predict_all(test_data)
    proba_preds = model_facade.predict_proba_all(test_data)

    # Check consistency
    for model in ["lstm", "xgb", "ensemble"]:
        assert np.allclose(binary_preds[model], (proba_preds[model] > 0.5).astype(int))
        assert all(0 <= p <= 1 for p in proba_preds[model])
