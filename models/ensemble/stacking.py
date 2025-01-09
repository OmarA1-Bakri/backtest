from typing import Dict, Any, Optional, List, Type
import numpy as np
from sklearn.model_selection import KFold
from datetime import datetime
from pathlib import Path
from base.model import BaseModel
from manager.manager import ModelManager
from traditional.xgboost_model import XGBoostModel


class StackingEnsemble(BaseModel):
    """Stacking ensemble model using cross-validation predictions."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Optional[Dict[str, Any]] = None,
        model_path: Optional[Path] = None,
    ):
        """Initialize stacking ensemble.

        Args:
            name: Model identifier
            features: Feature list
            model_params: Model parameters
            model_path: Path to save/load model
        """
        super().__init__(name, features, model_params, model_path)

        # Initialize model managers
        self.base_models = ModelManager()
        self.meta_model = None

        # Get ensemble parameters
        self.n_splits = self.model_params.get("n_splits", 5)
        self.shuffle = self.model_params.get("shuffle", True)
        self.random_state = self.model_params.get("random_state", 42)

        # Initialize cross-validator
        self.cv = KFold(
            n_splits=self.n_splits, shuffle=self.shuffle, random_state=self.random_state
        )

    def add_base_model(self, model: BaseModel) -> None:
        """Add a base model to the ensemble.

        Args:
            model: Model to add
        """
        self.base_models.register_model(
            name=model.name,
            model_class=model.__class__,
            features=model.features,
            model_params=model.model_params,
        )

    def set_meta_model(
        self,
        model_class: Type[BaseModel] = XGBoostModel,
        model_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Set the meta-model for stacking.

        Args:
            model_class: Meta-model class
            model_params: Meta-model parameters
        """
        self.meta_model = model_class(
            name=f"{self.name}_meta",
            features=[f"{name}_pred" for name in self.base_models.models],
            model_params=model_params,
        )

    def _get_meta_features(
        self, X: np.ndarray, y: np.ndarray = None, train: bool = True
    ) -> np.ndarray:
        """Generate meta-features using cross-validation predictions.

        Args:
            X: Input features
            y: Target values (only needed for training)
            train: Whether this is for training

        Returns:
            Meta-features array
        """
        n_samples = len(X)
        n_models = len(self.base_models.models)
        meta_features = np.zeros((n_samples, n_models))

        if train:
            # Generate cross-validation predictions
            for i, (train_idx, val_idx) in enumerate(self.cv.split(X)):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train = y[train_idx] if y is not None else None

                # Train base models on fold
                for j, (name, model) in enumerate(self.base_models.models.items()):
                    model.train(X_train, y_train)
                    meta_features[val_idx, j] = model.predict_proba(X_val)[:, 1]

            # Train base models on full dataset
            for name, model in self.base_models.models.items():
                model.train(X, y)

        else:
            # Use trained models to generate predictions
            for j, (name, model) in enumerate(self.base_models.models.items()):
                meta_features[:, j] = model.predict_proba(X)[:, 1]

        return meta_features

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the stacking ensemble.

        Args:
            X: Training features
            y: Training targets
        """
        if not self.base_models.models:
            raise RuntimeError("No base models added to ensemble")

        if self.meta_model is None:
            self.set_meta_model()

        # Generate meta-features
        meta_features = self._get_meta_features(X, y, train=True)

        # Train meta-model
        self.meta_model.train(meta_features, y)

        self.is_trained = True
        self.train_time = datetime.now().isoformat()

        # Store ensemble metadata
        self.metadata.update(
            {
                "base_models": list(self.base_models.models.keys()),
                "meta_model": self.meta_model.name,
                "n_splits": self.n_splits,
            }
        )

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate stacking ensemble predictions.

        Args:
            X: Input features

        Returns:
            Binary predictions
        """
        if not self.is_trained:
            raise RuntimeError("Ensemble must be trained before prediction")

        # Generate meta-features
        meta_features = self._get_meta_features(X, train=False)

        # Get meta-model predictions
        return self.meta_model.predict(meta_features)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate stacking ensemble probability predictions.

        Args:
            X: Input features

        Returns:
            Probability predictions
        """
        if not self.is_trained:
            raise RuntimeError("Ensemble must be trained before prediction")

        # Generate meta-features
        meta_features = self._get_meta_features(X, train=False)

        # Get meta-model probability predictions
        return self.meta_model.predict_proba(meta_features)

    def get_base_predictions(
        self, X: np.ndarray, proba: bool = False
    ) -> Dict[str, np.ndarray]:
        """Get individual base model predictions.

        Args:
            X: Input features
            proba: Whether to return probabilities

        Returns:
            Dictionary of model predictions
        """
        return self.base_models.predict_all(X, proba=proba)
