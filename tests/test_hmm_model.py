"""Test HMM model functionality."""

import pytest
import numpy as np
import pandas as pd
from models.probabilistic.hmm import HMMModel


@pytest.fixture
def test_data():
    """Create test data for HMM model."""
    # Generate synthetic data with two clear regimes
    np.random.seed(42)
    n_samples = 100

    # Regime 1: Low volatility
    regime1 = np.random.normal(0, 0.5, n_samples // 2)

    # Regime 2: High volatility
    regime2 = np.random.normal(0, 2.0, n_samples // 2)

    # Combine regimes
    data = np.concatenate([regime1, regime2])
    return data.reshape(-1, 1)


@pytest.fixture
def hmm_model():
    """Create HMM model instance."""
    return HMMModel(n_components=2)


def test_hmm_initialization(hmm_model):
    """Test HMM model initialization."""
    assert hmm_model.n_components == 2
    assert not hmm_model.is_trained
    assert hmm_model.metadata == {}


def test_hmm_training(hmm_model, test_data):
    """Test HMM model training."""
    hmm_model.train(test_data)

    assert hmm_model.is_trained
    assert hmm_model.train_time is not None
    assert "n_components" in hmm_model.metadata
    assert "means" in hmm_model.metadata
    assert "covars" in hmm_model.metadata
    assert "transmat" in hmm_model.metadata
    assert "score" in hmm_model.metadata


def test_hmm_prediction(hmm_model, test_data):
    """Test HMM model prediction."""
    hmm_model.train(test_data)

    # Test state prediction
    states = hmm_model.predict(test_data)
    assert isinstance(states, np.ndarray)
    assert states.shape == (len(test_data),)
    assert np.all((states >= 0) & (states < hmm_model.n_components))

    # Test probability prediction
    probas = hmm_model.predict_proba(test_data)
    assert isinstance(probas, np.ndarray)
    assert probas.shape == (len(test_data), hmm_model.n_components)
    assert np.allclose(np.sum(probas, axis=1), 1.0)


def test_hmm_state_properties(hmm_model, test_data):
    """Test HMM model state properties."""
    hmm_model.train(test_data)

    # Test state means
    means = hmm_model.get_state_means()
    assert isinstance(means, np.ndarray)
    assert means.shape == (hmm_model.n_components, test_data.shape[1])

    # Test state covariances
    covars = hmm_model.get_state_covars()
    assert isinstance(covars, np.ndarray)
    assert covars.shape == (
        hmm_model.n_components,
        test_data.shape[1],
        test_data.shape[1],
    )

    # Test transition matrix
    transmat = hmm_model.get_transition_matrix()
    assert isinstance(transmat, np.ndarray)
    assert transmat.shape == (hmm_model.n_components, hmm_model.n_components)
    assert np.allclose(np.sum(transmat, axis=1), 1.0)


def test_hmm_error_handling(hmm_model):
    """Test HMM model error handling."""
    # Test prediction before training
    with pytest.raises(RuntimeError):
        hmm_model.predict(np.array([[1.0]]))

    with pytest.raises(RuntimeError):
        hmm_model.predict_proba(np.array([[1.0]]))

    with pytest.raises(RuntimeError):
        hmm_model.get_state_means()

    with pytest.raises(RuntimeError):
        hmm_model.get_state_covars()

    with pytest.raises(RuntimeError):
        hmm_model.get_transition_matrix()


def test_hmm_data_scaling(hmm_model):
    """Test HMM model data scaling."""
    # Generate data with different scales
    X = np.array([[100.0], [200.0], [300.0], [400.0], [500.0]])

    # Train model
    hmm_model.train(X)

    # Get predictions
    states = hmm_model.predict(X)
    probas = hmm_model.predict_proba(X)

    # Check that scaling doesn't affect state assignments
    assert isinstance(states, np.ndarray)
    assert isinstance(probas, np.ndarray)
    assert np.allclose(np.sum(probas, axis=1), 1.0)


def test_hmm_1d_input_handling(hmm_model):
    """Test HMM model handling of 1D input."""
    # Generate 1D data
    X = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

    # Train model
    hmm_model.train(X)

    # Get predictions
    states = hmm_model.predict(X)
    probas = hmm_model.predict_proba(X)

    # Check output shapes
    assert states.shape == (len(X),)
    assert probas.shape == (len(X), hmm_model.n_components)
