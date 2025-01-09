"""Hidden Markov Model for regime detection."""

from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from hmmlearn import hmm
from datetime import datetime
from pathlib import Path
from models.base.model import BaseModel


class HMMModel(BaseModel):
    """Hidden Markov Model for regime detection."""

    def __init__(
        self,
        name: str = "hmm",
        n_components: int = 2,
        features: Optional[List[str]] = None,
        model_params: Optional[Dict[str, Any]] = None,
        model_path: Optional[Path] = None,
    ):
        """Initialize HMM model.

        Args:
            name: Model identifier
            n_components: Number of HMM states
            features: Feature list
            model_params: Model parameters
            model_path: Path to save/load model
        """
        super().__init__(name, features or [], model_path=model_path)
        self.n_components = n_components
        self.model_params = model_params or {}

        # Initialize HMM model
        self.model = hmm.GaussianHMM(
            n_components=self.n_components,
            covariance_type=self.model_params.get("covariance_type", "full"),
            n_iter=self.model_params.get("n_iter", 100),
            random_state=self.model_params.get("random_state", 42),
        )

    def train(self, X: np.ndarray, y: np.ndarray = None) -> None:
        """Train the HMM model.

        Args:
            X: Training features
            y: Ignored (unsupervised learning)
        """
        # Ensure data is correctly shaped
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)

        # Scale the data to prevent numerical instability
        self.data_mean = np.mean(X, axis=0)
        self.data_std = (
            np.std(X, axis=0) + 1e-6
        )  # Add small constant to prevent division by zero
        X_scaled = (X - self.data_mean) / self.data_std

        # Initialize model with reasonable starting values
        n_features = X_scaled.shape[1]

        # Initialize means using k-means-like approach
        indices = np.linspace(0, len(X_scaled) - 1, self.n_components, dtype=int)
        self.model.means_ = X_scaled[indices]

        # Initialize covariance matrices
        self.model.covars_ = np.array(
            [np.eye(n_features) for _ in range(self.n_components)]
        )

        # Initialize transition matrix
        self.model.transmat_ = (
            np.ones((self.n_components, self.n_components)) / self.n_components
        )

        # Initialize starting probabilities
        self.model.startprob_ = np.ones(self.n_components) / self.n_components

        try:
            # Train model with scaled data
            self.model.fit(X_scaled)

            # Update model statistics
            self.is_trained = True
            self.train_time = datetime.now().isoformat()

            # Store model statistics (in original scale)
            means_original = self.model.means_ * self.data_std + self.data_mean
            covars_original = self.model.covars_ * np.outer(
                self.data_std, self.data_std
            )

            self.metadata.update(
                {
                    "n_components": self.n_components,
                    "means": means_original.tolist(),
                    "covars": covars_original.tolist(),
                    "transmat": self.model.transmat_.tolist(),
                    "score": float(self.model.score(X_scaled)),
                }
            )
        except Exception as e:
            self.is_trained = False
            raise RuntimeError(f"HMM training failed: {str(e)}")

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict regime states.

        Args:
            X: Input features

        Returns:
            Predicted regime states
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        # Ensure data is correctly shaped
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)

        # Scale the input data
        X_scaled = (X - self.data_mean) / self.data_std

        try:
            return self.model.predict(X_scaled)
        except Exception as e:
            # Return most common state if prediction fails
            return np.zeros(len(X), dtype=int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict regime probabilities.

        Args:
            X: Input features

        Returns:
            Regime probabilities
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        # Ensure data is correctly shaped
        if len(X.shape) == 1:
            X = X.reshape(-1, 1)

        # Scale the input data
        X_scaled = (X - self.data_mean) / self.data_std

        try:
            return self.model.predict_proba(X_scaled)
        except Exception as e:
            # Return uniform probabilities if prediction fails
            return np.full((len(X), self.n_components), 1.0 / self.n_components)

    def get_state_means(self) -> np.ndarray:
        """Get state means.

        Returns:
            State means
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before getting state means")
        return self.model.means_ * self.data_std + self.data_mean

    def get_state_covars(self) -> np.ndarray:
        """Get state covariance matrices.

        Returns:
            State covariance matrices
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before getting state covariances")
        return self.model.covars_ * np.outer(self.data_std, self.data_std)

    def get_transition_matrix(self) -> np.ndarray:
        """Get state transition matrix.

        Returns:
            State transition matrix
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before getting transition matrix")
        return self.model.transmat_
