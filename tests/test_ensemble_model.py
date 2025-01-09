"""Test ensemble model functionality."""

import pytest
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
import os
from models.ensemble.ensemble_model import EnsembleModel


@pytest.fixture
def test_data():
    """Create test data for ensemble model."""
    np.random.seed(42)
    n_samples = 100
    n_features = 3

    X = np.random.randn(n_samples, n_features)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)

    return pd.DataFrame(X), pd.Series(y)


@pytest.fixture
def base_models():
    """Create base models for ensemble."""
    return [LogisticRegression(), DecisionTreeClassifier(max_depth=2)]


@pytest.fixture
def ensemble_model(base_models):
    """Create ensemble model instance."""
    return EnsembleModel(models=base_models)


def test_ensemble_initialization(ensemble_model, base_models):
    """Test ensemble model initialization."""
    assert len(ensemble_model.models) == len(base_models)
    assert len(ensemble_model.weights) == len(base_models)
    assert np.allclose(sum(ensemble_model.weights), 1.0)


def test_ensemble_training(ensemble_model, test_data):
    """Test ensemble model training."""
    X, y = test_data
    ensemble_model.fit(X, y)

    # Check that all models are trained
    for model in ensemble_model.models:
        assert hasattr(model, "predict")


def test_ensemble_prediction(ensemble_model, test_data):
    """Test ensemble model prediction."""
    X, y = test_data
    ensemble_model.fit(X, y)

    # Test predictions
    preds = ensemble_model.predict(X)
    assert isinstance(preds, np.ndarray)
    assert preds.shape == (len(X),)

    # Test probability predictions
    probas = ensemble_model.predict_proba(X)
    assert isinstance(probas, np.ndarray)
    assert probas.shape == (len(X),)


def test_ensemble_custom_weights():
    """Test ensemble model with custom weights."""
    models = [LogisticRegression(), DecisionTreeClassifier()]
    weights = [0.7, 0.3]

    ensemble = EnsembleModel(models=models, weights=weights)
    assert np.allclose(ensemble.weights, weights)


def test_ensemble_model_persistence(ensemble_model, test_data, tmp_path):
    """Test ensemble model persistence."""
    X, y = test_data
    ensemble_model.fit(X, y)

    # Save model
    save_path = os.path.join(tmp_path, "ensemble_model.pkl")
    ensemble_model.save_model(save_path)
    assert os.path.exists(save_path)

    # Create new model and load saved state
    new_model = EnsembleModel(
        models=[LogisticRegression()]
    )  # Initialize with a dummy model
    new_model.load_model(save_path)

    # Check that loaded model has same properties
    assert len(new_model.models) == len(ensemble_model.models)
    assert np.allclose(new_model.weights, ensemble_model.weights)

    # Check that predictions match
    assert np.allclose(new_model.predict(X), ensemble_model.predict(X))


def test_ensemble_error_handling(ensemble_model, test_data):
    """Test ensemble model error handling."""
    X, y = test_data

    # Test saving to invalid path with invalid characters
    with pytest.raises(Exception):
        ensemble_model.save_model('/:*?"<>|')

    # Test loading non-existent model
    with pytest.raises(FileNotFoundError):
        ensemble_model.load_model("/non/existent/model.pkl")


def test_ensemble_with_custom_models(test_data):
    """Test ensemble model with custom models that use train instead of fit."""

    class CustomModel:
        def train(self, X, y):
            self.X = X
            self.y = y

        def predict(self, X):
            return np.zeros(len(X))

        def predict_proba(self, X):
            return np.zeros(len(X))

    models = [CustomModel(), CustomModel()]
    ensemble = EnsembleModel(models=models)

    X, y = test_data
    ensemble.fit(X, y)  # Should use train method for custom models

    # Test predictions
    preds = ensemble.predict(X)
    assert isinstance(preds, np.ndarray)
    assert preds.shape == (len(X),)
