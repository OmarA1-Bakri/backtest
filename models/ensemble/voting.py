from typing import Dict, Any, Optional, List
import numpy as np
from datetime import datetime
from pathlib import Path
from base.model import BaseModel
from manager.manager import ModelManager


class VotingEnsemble(BaseModel):
    """Voting ensemble model combining multiple base models."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Optional[Dict[str, Any]] = None,
        model_path: Optional[Path] = None,
    ):
        """Initialize voting ensemble.

        Args:
            name: Model identifier
            features: Feature list
            model_params: Model parameters including weights
            model_path: Path to save/load model
        """
        super().__init__(name, features, model_params, model_path)

        # Initialize model manager
        self.model_manager = ModelManager()

        # Get ensemble parameters
        self.weights = self.model_params.get("weights", {})
        self.voting = self.model_params.get("voting", "soft")  # 'hard' or 'soft'
        self.threshold = self.model_params.get("threshold", 0.5)

    def add_model(self, model: BaseModel, weight: float = 1.0) -> None:
        """Add a model to the ensemble.

        Args:
            model: Model to add
            weight: Model weight in ensemble
        """
        self.model_manager.register_model(
            name=model.name,
            model_class=model.__class__,
            features=model.features,
            model_params=model.model_params,
        )
        self.weights[model.name] = weight

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train all models in the ensemble.

        Args:
            X: Training features
            y: Training targets
        """
        # Train all models
        self.model_manager.train_all(X, y, parallel=True)

        self.is_trained = True
        self.train_time = datetime.now().isoformat()

        # Store ensemble metadata
        self.metadata.update(
            {
                "models": list(self.weights.keys()),
                "weights": self.weights,
                "voting": self.voting,
            }
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate ensemble predictions.

        Args:
            X: Input features

        Returns:
            Binary predictions
        """
        if not self.is_trained:
            raise RuntimeError("Ensemble must be trained before prediction")

        if self.voting == "hard":
            # Get individual predictions
            predictions = self.model_manager.predict_all(X)

            # Apply weights and sum
            weighted_votes = np.zeros(len(X))
            total_weight = sum(self.weights.values())

            for name, preds in predictions.items():
                weight = self.weights.get(name, 1.0)
                weighted_votes += (weight / total_weight) * preds

            return (weighted_votes > self.threshold).astype(int)

        else:  # soft voting
            # Get probability predictions
            probas = self.predict_proba(X)
            return (probas > self.threshold).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate ensemble probability predictions.

        Args:
            X: Input features

        Returns:
            Probability predictions
        """
        if not self.is_trained:
            raise RuntimeError("Ensemble must be trained before prediction")

        # Get individual probability predictions
        predictions = self.model_manager.predict_all(X, proba=True)

        # Apply weights and average
        weighted_probas = np.zeros((len(X), 2))
        total_weight = sum(self.weights.values())

        for name, probas in predictions.items():
            weight = self.weights.get(name, 1.0)
            weighted_probas += (weight / total_weight) * probas

        return weighted_probas

    def get_model_weights(self) -> Dict[str, float]:
        """Get current model weights.

        Returns:
            Dictionary of model weights
        """
        return self.weights.copy()

    def set_model_weights(self, weights: Dict[str, float]) -> None:
        """Set model weights.

        Args:
            weights: Dictionary of model weights
        """
        # Validate weights
        if not all(name in self.model_manager.models for name in weights):
            raise ValueError("Invalid model name in weights")

        self.weights = weights.copy()
        self.metadata["weights"] = self.weights

    def get_model_predictions(
        self, X: np.ndarray, proba: bool = False
    ) -> Dict[str, np.ndarray]:
        """Get individual model predictions.

        Args:
            X: Input features
            proba: Whether to return probabilities

        Returns:
            Dictionary of model predictions
        """
        return self.model_manager.predict_all(X, proba=proba)
