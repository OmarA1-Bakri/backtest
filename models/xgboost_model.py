"""XGBoost model implementation."""

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import xgboost as xgb


class XGBoostModel:
    """XGBoost model for time series prediction."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Dict[str, Any],
        model_path: Path,
    ):
        """Initialize XGBoost model.

        Args:
            name: Model name
            features: List of feature names
            model_params: Model parameters
            model_path: Path to save model
        """
        self.name = name
        self.features = features
        self.model_path = model_path
        self.model_params = model_params

        # Extract model parameters with defaults
        self.max_depth = model_params.get("max_depth", 3)
        self.learning_rate = model_params.get("learning_rate", 0.1)
        self.n_estimators = model_params.get("n_estimators", 100)
        self.objective = model_params.get("objective", "reg:squarederror")
        self.booster = model_params.get("booster", "gbtree")
        self.subsample = model_params.get("subsample", 0.8)
        self.colsample_bytree = model_params.get("colsample_bytree", 0.8)
        self.min_child_weight = model_params.get("min_child_weight", 1)
        self.gamma = model_params.get("gamma", 0)
        self.reg_alpha = model_params.get("reg_alpha", 0)
        self.reg_lambda = model_params.get("reg_lambda", 1)
        self.early_stopping_rounds = model_params.get("early_stopping_rounds", 10)

        # Build model
        self.model = self._build_model()

    def _build_model(self) -> xgb.XGBRegressor:
        """Build XGBoost model.

        Returns:
            Built model
        """
        return xgb.XGBRegressor(
            max_depth=self.max_depth,
            learning_rate=self.learning_rate,
            n_estimators=self.n_estimators,
            objective=self.objective,
            booster=self.booster,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            min_child_weight=self.min_child_weight,
            gamma=self.gamma,
            reg_alpha=self.reg_alpha,
            reg_lambda=self.reg_lambda,
            early_stopping_rounds=self.early_stopping_rounds,
            random_state=42,
        )

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train the model.

        Args:
            X_train: Training features
            y_train: Training labels
        """
        # Create validation set
        val_size = int(len(X_train) * 0.2)
        X_val = X_train[-val_size:]
        y_val = y_train[-val_size:]
        X_train = X_train[:-val_size]
        y_train = y_train[:-val_size]

        # Train model
        self.model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            verbose=True,
        )

        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(str(self.model_path))

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions.

        Args:
            X: Input features

        Returns:
            Predictions
        """
        return self.model.predict(X)
