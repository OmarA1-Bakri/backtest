from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
import numpy as np
import pandas as pd
from datetime import datetime
import joblib
from pathlib import Path


class BaseModel(ABC):
    """Abstract base class for all models in the system."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Optional[Dict[str, Any]] = None,
        model_path: Optional[Union[str, Path]] = None,
    ):
        """Initialize base model.

        Args:
            name: Model identifier
            features: List of feature names
            model_params: Model-specific parameters
            model_path: Path to save/load model
        """
        self.name = name
        self.features = features
        self.model_params = model_params or {}
        self.model_path = Path(model_path) if model_path else None
        self.model = None
        self.is_trained = False
        self.train_time = None
        self.metadata = {}

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the model.

        Args:
            X: Training features
            y: Training targets
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions.

        Args:
            X: Input features

        Returns:
            Model predictions
        """
        pass

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate probability predictions.

        Args:
            X: Input features

        Returns:
            Probability predictions
        """
        return self.predict(X)

    def save(self, path: Optional[Union[str, Path]] = None) -> Path:
        """Save model to disk.

        Args:
            path: Save path (optional)

        Returns:
            Path where model was saved
        """
        save_path = Path(path) if path else self.model_path
        if save_path is None:
            raise ValueError("No save path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Save metadata
        self.metadata.update(
            {
                "name": self.name,
                "features": self.features,
                "params": self.model_params,
                "is_trained": self.is_trained,
                "train_time": self.train_time,
                "save_time": datetime.now().isoformat(),
            }
        )

        # Save model and metadata
        joblib.dump({"model": self.model, "metadata": self.metadata}, save_path)

        return save_path

    def load(self, path: Optional[Union[str, Path]] = None) -> None:
        """Load model from disk.

        Args:
            path: Load path (optional)
        """
        load_path = Path(path) if path else self.model_path
        if load_path is None:
            raise ValueError("No load path specified")

        if not load_path.exists():
            raise FileNotFoundError(f"Model file not found: {load_path}")

        # Load model and metadata
        data = joblib.load(load_path)
        self.model = data["model"]
        self.metadata = data["metadata"]

        # Restore metadata
        self.name = self.metadata["name"]
        self.features = self.metadata["features"]
        self.model_params = self.metadata["params"]
        self.is_trained = self.metadata["is_trained"]
        self.train_time = self.metadata["train_time"]

    def get_params(self) -> Dict[str, Any]:
        """Get model parameters.

        Returns:
            Dictionary of model parameters
        """
        return {
            "name": self.name,
            "features": self.features,
            "model_params": self.model_params,
            "is_trained": self.is_trained,
            "train_time": self.train_time,
            "metadata": self.metadata,
        }

    def validate_features(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """Validate and prepare input features.

        Args:
            X: Input features

        Returns:
            Validated numpy array
        """
        if isinstance(X, pd.DataFrame):
            if not all(f in X.columns for f in self.features):
                missing = set(self.features) - set(X.columns)
                raise ValueError(f"Missing features: {missing}")
            X = X[self.features].values

        if not isinstance(X, np.ndarray):
            raise TypeError(f"Expected numpy array or DataFrame, got {type(X)}")

        if X.shape[1] != len(self.features):
            raise ValueError(
                f"Expected {len(self.features)} features, got {X.shape[1]}"
            )

        return X
