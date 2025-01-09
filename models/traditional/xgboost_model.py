from typing import Dict, Any, Optional, List
import xgboost as xgb
from datetime import datetime
from pathlib import Path
from models.base.model import BaseModel
import os


class XGBoostModel(BaseModel):
    """XGBoost model for classification."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Optional[Dict[str, Any]] = None,
        model_path: Optional[Path] = None,
    ):
        """Initialize XGBoost model.

        Args:
            name: Model identifier
            features: Feature list
            model_params: Model parameters
            model_path: Path to save/load model
        """
        super().__init__(name, features, model_params, model_path)

        # Default XGBoost parameters
        self.xgb_params = {
            "objective": "binary:logistic",
            "eval_metric": "logloss",
            "max_depth": 6,
            "eta": 0.3,
            "n_estimators": 100,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "min_child_weight": 1,
            "gamma": 0,
            "random_state": 42,
            **self.model_params,
        }

        self.model = xgb.XGBClassifier(**self.xgb_params)

    def train(self, X, y):
        """Train the XGBoost model.

        Args:
            X: Training features
            y: Training targets
        """
        # Training parameters
        eval_size = self.model_params.get("eval_size", 0.2)
        early_stopping_rounds = self.model_params.get("early_stopping_rounds", 10)

        # Split data for evaluation
        train_size = int(len(X) * (1 - eval_size))
        X_train, X_eval = X[:train_size], X[train_size:]
        y_train = y[:train_size]  # , y_eval = y[train_size:]

        # Create evaluation set
        eval_set = [
            (X_train, y_train),
            (X_eval, y_train[: len(X_eval)]),  # Fixed label size to match X_eval size
        ]

        # Train model
        self.model.fit(
            X_train,
            y_train,
            eval_set=eval_set,
            early_stopping_rounds=early_stopping_rounds,
            verbose=False,
        )

        self.is_trained = True
        self.train_time = datetime.now().isoformat()

        # Store feature importance
        self.metadata["feature_importance"] = {
            feature: importance
            for feature, importance in zip(
                self.features, self.model.feature_importances_
            )
        }

    def predict_proba(self, X):
        if self.model is None:
            raise ValueError("Model has not been trained. Call train() first.")
        return self.model.predict_proba(X)[:, 1]

    def predict(self, X, threshold=0.5):
        """
        Predicts class labels based on probabilities and a threshold.

        Parameters:
        - X (pd.DataFrame or np.ndarray): Feature matrix.
        - threshold (float): Threshold for converting probabilities to class labels.

        Returns:
        - np.ndarray: Predicted class labels.
        """
        proba = self.predict_proba(X)
        return (proba >= threshold).astype(int)

    def save_model(self):
        """
        Saves the trained model to the specified path.
        """
        if self.model is None:
            raise ValueError("No model to save. Train the model first.")
        self.model.save_model(self.model_path)

    def load_model(self):
        """
        Loads the model from the specified path.
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No saved model found at {self.model_path}")
        self.model = xgb.Booster()
        self.model.load_model(self.model_path)

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance scores.

        Returns:
            Dictionary of feature importance scores
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained to get feature importance")

        return self.metadata.get("feature_importance", {})
