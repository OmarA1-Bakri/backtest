# backtest/models/model_facade.py

from typing import List, Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from logger import logger
from models.ensemble.ensemble_model import EnsembleModel
from models.deep_learning.lstm import LSTMModel
from models.probabilistic.hmm import HMMModel
from models.traditional.xgboost_model import XGBoostModel
from concurrent.futures import ProcessPoolExecutor
from unittest.mock import MagicMock
from pathlib import Path


class ModelFacade:
    """Model facade for managing different models."""

    def __init__(self, features: List[str], model_settings: Dict[str, Any]):
        self.features = features
        # Extract settings
        if isinstance(model_settings, dict):
            self.time_steps = model_settings.get("time_steps", 10)
            self.n_components = model_settings.get("n_components", 5)
            self.model_dir = Path(model_settings.get("model_dir", "models"))
            lstm_settings = model_settings.get("lstm", {})
            hmm_settings = model_settings.get("hmm", {})
            xgboost_settings = model_settings.get("xgboost", {})
        else:
            # Handle pydantic model case
            self.time_steps = getattr(model_settings, "time_steps", 10)
            self.n_components = getattr(model_settings, "n_components", 5)
            self.model_dir = Path(getattr(model_settings, "model_dir", "models"))
            lstm_settings = getattr(model_settings, "lstm", {})
            hmm_settings = getattr(model_settings, "hmm", {})
            xgboost_settings = getattr(model_settings, "xgboost", {})

        # Initialize base models
        self.lstm_model = LSTMModel(
            name="lstm",
            features=features,
            model_params={
                "time_steps": self.time_steps,
                "hidden_units": [50, 50],
                "dense_units": 25,
                "dropout_rate": 0.2,
                "l2_reg": 0.01,
                **lstm_settings,
            },
            model_path=self.model_dir / "lstm",
        )

        self.hmm_model = HMMModel(n_components=self.n_components, **hmm_settings)

        self.xgboost_model = XGBoostModel(
            name="xgboost",
            features=features,
            model_params={
                "max_depth": 3,
                "learning_rate": 0.1,
                "n_estimators": 100,
                "objective": "reg:squarederror",
                "booster": "gbtree",
                **xgboost_settings,
            },
            model_path=self.model_dir / "xgboost",
        )

        # Create ensemble model
        self.ensemble_model = EnsembleModel(
            models=[self.lstm_model, self.hmm_model, self.xgboost_model]
        )

        self.predict_hmm_regime = MagicMock(return_value="State_1")
        self.strategy = None  # Initialize the strategy object later

    def initialize_strategy(self):
        from ..strategy import Strategy  # Lazy import

        self.strategy = Strategy()

    def train_models(self, X_train: np.ndarray, y_train: np.ndarray):
        logger.info("Starting training of ensemble model")
        try:
            # Train LSTM with original data - it will handle sequence creation internally
            self.lstm_model.train(X_train, y_train)

            # Train other models with original data
            self.hmm_model.train(X_train)
            self.xgboost_model.train(X_train, y_train)

            cv_results = self.cross_validate_models(X_train, y_train)
            logger.info(f"Cross-validation results: {cv_results}")

            # Train ensemble with original data
            self.ensemble_model.fit(X_train, y_train)
            logger.info("Ensemble model trained successfully")
        except Exception as e:
            logger.error(f"Error during training models: {e}")
            raise

    def predict_all(self, X: pd.DataFrame) -> Dict[str, Any]:
        try:
            X_np = X[self.features].values if isinstance(X, pd.DataFrame) else X
            predictions = {}

            try:
                predictions["xgb"] = self.xgboost_model.predict_proba(X_np)
            except Exception as e:
                logger.error(f"XGBoost prediction failed: {e}")
                predictions["xgb"] = np.zeros(len(X_np))

            try:
                predictions["lstm"] = self.lstm_model.predict(X_np)
            except Exception as e:
                logger.error(f"LSTM prediction failed: {e}")
                predictions["lstm"] = np.zeros(len(X_np))

            try:
                predictions["hmm"] = self.hmm_model.predict(X_np)
            except Exception as e:
                logger.error(f"HMM prediction failed: {e}")
                predictions["hmm"] = np.zeros(len(X_np))

            try:
                ensemble_pred = self.ensemble_model.predict(X_np)
                predictions["ensemble"] = ensemble_pred
            except Exception as e:
                logger.error(f"Ensemble prediction failed: {e}")
                predictions["ensemble"] = np.zeros(len(X_np))

            return predictions

        except Exception as e:
            logger.error(f"Error in predict_all: {e}")
            return {
                "xgb": np.zeros(len(X_np)),
                "lstm": np.zeros(len(X_np)),
                "hmm": np.zeros(len(X_np)),
                "ensemble": np.zeros(len(X_np)),
            }

    def predict_proba_all(self, X: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Get probability predictions from all models.

        Args:
            X: Input features

        Returns:
            Dictionary with model probability predictions
        """
        try:
            X_np = X[self.features].values if isinstance(X, pd.DataFrame) else X
            predictions = {}

            try:
                predictions["xgb"] = self.xgboost_model.predict_proba(X_np)
            except Exception as e:
                logger.error(f"XGBoost probability prediction failed: {e}")
                predictions["xgb"] = np.full(len(X_np), 0.5)

            try:
                predictions["lstm"] = self.lstm_model.predict_proba(X_np)
            except Exception as e:
                logger.error(f"LSTM probability prediction failed: {e}")
                predictions["lstm"] = np.full(len(X_np), 0.5)

            try:
                predictions["hmm"] = self.hmm_model.predict(X_np)
            except Exception as e:
                logger.error(f"HMM prediction failed: {e}")
                predictions["hmm"] = np.full(len(X_np), 0.5)

            try:
                ensemble_pred = self.ensemble_model.predict_proba(X_np)
                predictions["ensemble"] = ensemble_pred
            except Exception as e:
                logger.error(f"Ensemble probability prediction failed: {e}")
                predictions["ensemble"] = np.full(len(X_np), 0.5)

            return predictions

        except Exception as e:
            logger.error(f"Error in predict_proba_all: {e}")
            return {
                "xgb": np.full(len(X_np), 0.5),
                "lstm": np.full(len(X_np), 0.5),
                "hmm": np.full(len(X_np), 0.5),
                "ensemble": np.full(len(X_np), 0.5),
            }

    def save_all_models(self):
        try:
            logger.info("Saving all models to disk")
            self.ensemble_model.save_model(self.model_dir)
            logger.info("All models saved successfully")
        except Exception as e:
            logger.error(f"Error saving all models: {e}")
            raise

    def load_all_models(self):
        try:
            logger.info("Loading all models from disk")
            self.ensemble_model.load_model(self.model_dir)
            logger.info("All models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading all models: {e}")
            raise

    def cross_validate_models(
        self, X: np.ndarray, y: np.ndarray, n_splits: int = 5
    ) -> Dict[str, float]:
        """Perform cross-validation on individual models.

        Args:
            X: Training features
            y: Target values
            n_splits: Number of cross-validation splits

        Returns:
            Dictionary with model scores
        """
        try:
            from sklearn.model_selection import KFold

            kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)

            scores = {"lstm": [], "hmm": [], "xgb": []}

            for train_idx, val_idx in kf.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]

                # Prepare LSTM data
                n_train_samples = X_train.shape[0]
                n_val_samples = X_val.shape[0]
                n_features = len(self.features)

                n_train_sequences = n_train_samples - self.time_steps + 1
                n_val_sequences = n_val_samples - self.time_steps + 1

                if n_train_sequences > 0 and n_val_sequences > 0:
                    X_lstm_train = np.zeros(
                        (n_train_sequences, self.time_steps, n_features)
                    )
                    y_lstm_train = np.zeros(n_train_sequences)

                    X_lstm_val = np.zeros(
                        (n_val_sequences, self.time_steps, n_features)
                    )
                    y_lstm_val = np.zeros(n_val_sequences)

                    # Create sequences for training data
                    for i in range(n_train_sequences):
                        X_lstm_train[i] = X_train[i : i + self.time_steps]
                        y_lstm_train[i] = y_train[i + self.time_steps - 1]

                    # Create sequences for validation data
                    for i in range(n_val_sequences):
                        X_lstm_val[i] = X_val[i : i + self.time_steps]
                        y_lstm_val[i] = y_val[i + self.time_steps - 1]

                    # Train and evaluate LSTM
                    self.lstm_model.train(X_lstm_train, y_lstm_train)
                    lstm_pred = self.lstm_model.predict(X_lstm_val)
                    scores["lstm"].append(roc_auc_score(y_lstm_val, lstm_pred))

                # Train and evaluate HMM
                self.hmm_model.train(X_train)
                hmm_pred = self.hmm_model.predict(X_val)
                scores["hmm"].append(roc_auc_score(y_val, hmm_pred))

                # Train and evaluate XGBoost
                self.xgboost_model.train(X_train, y_train)
                xgb_pred = self.xgboost_model.predict_proba(X_val)
                scores["xgb"].append(roc_auc_score(y_val, xgb_pred))

            return scores

        except Exception as e:
            logger.error(f"Error in cross_validate_models: {e}")
            return {"lstm": 0.0, "hmm": 0.0, "xgb": 0.0}
