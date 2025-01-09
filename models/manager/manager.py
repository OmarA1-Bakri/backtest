from typing import Dict, Type, Optional, List, Any, Union
import numpy as np
import pandas as pd
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor
from base.model import BaseModel

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model lifecycle, training, and predictions."""

    def __init__(
        self, model_dir: Optional[Union[str, Path]] = None, max_workers: int = 4
    ):
        """Initialize model manager.

        Args:
            model_dir: Directory for model storage
            max_workers: Maximum number of parallel workers
        """
        self.model_dir = Path(model_dir) if model_dir else None
        self.max_workers = max_workers
        self.models: Dict[str, BaseModel] = {}
        self.model_registry: Dict[str, Type[BaseModel]] = {}

    def register_model(
        self,
        name: str,
        model_class: Type[BaseModel],
        features: List[str],
        model_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a model with the manager.

        Args:
            name: Model identifier
            model_class: Model class to register
            features: Feature list for the model
            model_params: Model-specific parameters
        """
        if name in self.model_registry:
            logger.warning(f"Overwriting existing model registration: {name}")

        self.model_registry[name] = model_class
        model_path = self.model_dir / f"{name}.joblib" if self.model_dir else None

        self.models[name] = model_class(
            name=name,
            features=features,
            model_params=model_params,
            model_path=model_path,
        )

    def train_model(
        self,
        name: str,
        X: Union[np.ndarray, pd.DataFrame],
        y: np.ndarray,
        save: bool = True,
    ) -> None:
        """Train a specific model.

        Args:
            name: Model identifier
            X: Training features
            y: Training targets
            save: Whether to save the model after training
        """
        if name not in self.models:
            raise KeyError(f"Model not registered: {name}")

        model = self.models[name]
        X_valid = model.validate_features(X)

        logger.info(f"Training model: {name}")
        model.train(X_valid, y)

        if save and model.model_path:
            model.save()

    def train_all(
        self, X: Union[np.ndarray, pd.DataFrame], y: np.ndarray, parallel: bool = True
    ) -> None:
        """Train all registered models.

        Args:
            X: Training features
            y: Training targets
            parallel: Whether to train models in parallel
        """
        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = [
                    executor.submit(self.train_model, name, X, y)
                    for name in self.models
                ]
                for future in futures:
                    future.result()  # Raises any exceptions that occurred
        else:
            for name in self.models:
                self.train_model(name, X, y)

    def predict(
        self, name: str, X: Union[np.ndarray, pd.DataFrame], proba: bool = False
    ) -> np.ndarray:
        """Generate predictions from a specific model.

        Args:
            name: Model identifier
            X: Input features
            proba: Whether to return probability predictions

        Returns:
            Model predictions
        """
        if name not in self.models:
            raise KeyError(f"Model not registered: {name}")

        model = self.models[name]
        X_valid = model.validate_features(X)

        if proba:
            return model.predict_proba(X_valid)
        return model.predict(X_valid)

    def predict_all(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        proba: bool = False,
        parallel: bool = True,
    ) -> Dict[str, np.ndarray]:
        """Generate predictions from all models.

        Args:
            X: Input features
            proba: Whether to return probability predictions
            parallel: Whether to generate predictions in parallel

        Returns:
            Dictionary of model predictions
        """
        predictions = {}

        if parallel:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    name: executor.submit(self.predict, name, X, proba)
                    for name in self.models
                }
                for name, future in futures.items():
                    predictions[name] = future.result()
        else:
            for name in self.models:
                predictions[name] = self.predict(name, X, proba)

        return predictions

    def load_model(self, name: str, path: Optional[Union[str, Path]] = None) -> None:
        """Load a model from disk.

        Args:
            name: Model identifier
            path: Optional path override
        """
        if name not in self.models:
            raise KeyError(f"Model not registered: {name}")

        self.models[name].load(path)

    def load_all(self) -> None:
        """Load all models from disk."""
        for name in self.models:
            try:
                self.load_model(name)
            except (FileNotFoundError, ValueError) as e:
                logger.warning(f"Failed to load model {name}: {e}")

    def save_model(self, name: str, path: Optional[Union[str, Path]] = None) -> None:
        """Save a model to disk.

        Args:
            name: Model identifier
            path: Optional path override
        """
        if name not in self.models:
            raise KeyError(f"Model not registered: {name}")

        self.models[name].save(path)

    def save_all(self) -> None:
        """Save all models to disk."""
        for name in self.models:
            try:
                self.save_model(name)
            except ValueError as e:
                logger.warning(f"Failed to save model {name}: {e}")

    def get_model(self, name: str) -> BaseModel:
        """Get a specific model instance.

        Args:
            name: Model identifier

        Returns:
            Model instance
        """
        if name not in self.models:
            raise KeyError(f"Model not registered: {name}")

        return self.models[name]

    def get_all_models(self) -> Dict[str, BaseModel]:
        """Get all model instances.

        Returns:
            Dictionary of model instances
        """
        return self.models.copy()
