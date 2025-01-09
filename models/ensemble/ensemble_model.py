from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import VotingClassifier, StackingClassifier
from sklearn.base import BaseEstimator
from logger import logger
import pickle
import os


class EnsembleModel(BaseEstimator):
    """Base class for ensemble models."""

    def __init__(self, models: List[BaseEstimator], weights: List[float] = None):
        """Initialize the ensemble model.

        Args:
            models: List of base models to ensemble
            weights: Optional weights for each model's prediction
        """
        self.models = models
        self.weights = weights if weights else [1.0 / len(models)] * len(models)

    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit each model in the ensemble.

        Args:
            X: Training features
            y: Target values
        """
        try:
            for model in self.models:
                if hasattr(model, "train"):
                    # LSTM and other custom models
                    model.train(X, y)
                else:
                    # Scikit-learn compatible models
                    model.fit(X, y)
        except Exception as e:
            logger.error(f"Error fitting ensemble model: {str(e)}")
            raise

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make predictions using weighted average of model predictions.

        Args:
            X: Features to predict on

        Returns:
            Weighted average predictions
        """
        try:
            predictions = []
            for model, weight in zip(self.models, self.weights):
                if hasattr(model, "predict_proba"):
                    # Use predict_proba for models that support it
                    pred = (
                        model.predict_proba(X)[:, 1]
                        if len(model.predict_proba(X).shape) > 1
                        else model.predict(X)
                    )
                else:
                    # Use regular predict for other models
                    pred = model.predict(X)
                predictions.append(pred * weight)

            return np.sum(predictions, axis=0)
        except Exception as e:
            logger.error(f"Error making ensemble predictions: {str(e)}")
            raise

    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Get probability predictions from ensemble.

        Args:
            X: Features to predict probabilities for

        Returns:
            Weighted average probability predictions
        """
        try:
            probas = []
            for model, weight in zip(self.models, self.weights):
                if hasattr(model, "predict_proba"):
                    prob = model.predict_proba(X)
                    if len(prob.shape) > 1:
                        prob = prob[:, 1]  # Take positive class probability
                    probas.append(prob * weight)
                else:
                    # For models without predict_proba, use predict
                    pred = model.predict(X)
                    probas.append(pred * weight)

            return np.sum(probas, axis=0) if probas else None
        except Exception as e:
            logger.error(f"Error getting ensemble probabilities: {str(e)}")
            raise

    def save_model(self, filepath: str) -> None:
        """Save the ensemble model to a file.

        Args:
            filepath: Path to save the model to
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # Save model state
            model_state = {"models": self.models, "weights": self.weights}

            with open(filepath, "wb") as f:
                pickle.dump(model_state, f)

            logger.info(f"Successfully saved ensemble model to {filepath}")
        except Exception as e:
            logger.error(f"Error saving ensemble model: {str(e)}")
            raise

    def load_model(self, filepath: str) -> None:
        """Load the ensemble model from a file.

        Args:
            filepath: Path to load the model from
        """
        try:
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Model file not found at {filepath}")

            with open(filepath, "rb") as f:
                model_state = pickle.load(f)

            self.models = model_state["models"]
            self.weights = model_state["weights"]

            logger.info(f"Successfully loaded ensemble model from {filepath}")
        except Exception as e:
            logger.error(f"Error loading ensemble model: {str(e)}")
            raise
