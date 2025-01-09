from typing import Dict, Any, Optional, List
import tensorflow as tf
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from keras.callbacks import EarlyStopping
from datetime import datetime
from pathlib import Path
from ..base.model import BaseModel
import numpy as np


class LSTMModel(BaseModel):
    """LSTM model for time series prediction."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Optional[Dict[str, Any]] = None,
        model_path: Optional[Path] = None,
    ):
        """Initialize LSTM model.

        Args:
            name: Model identifier
            features: Feature list
            model_params: Model parameters
            model_path: Path to save/load model
        """
        super().__init__(name, features, model_params, model_path)

        # Default parameters
        self.time_steps = self.model_params.get("time_steps", 60)
        self.hidden_units = self.model_params.get("hidden_units", [50, 50])
        self.dense_units = self.model_params.get("dense_units", 25)
        self.dropout_rate = self.model_params.get("dropout_rate", 0.2)
        self.l2_reg = self.model_params.get("l2_reg", 0.01)
        self.sequence_length = self.time_steps
        self.n_features = len(self.features)
        self.units = self.hidden_units[0]
        self.activation = "relu"
        self.dropout = self.dropout_rate
        self.optimizer = "adam"
        self.loss = "binary_crossentropy"
        self.metrics = ["accuracy"]
        self.epochs = self.model_params.get("epochs", 50)
        self.batch_size = self.model_params.get("batch_size", 32)

        self.model = self._build_model()

    def _build_model(self) -> Sequential:
        """Build and compile the LSTM model."""
        model = Sequential()

        # Input shape should be (timesteps, features)
        model.add(
            LSTM(
                units=self.units,
                activation=self.activation,
                input_shape=(self.sequence_length, self.n_features),
                return_sequences=True,
            )
        )
        model.add(Dropout(self.dropout))

        model.add(LSTM(units=self.units // 2, activation=self.activation))
        model.add(Dropout(self.dropout))

        # Dense layers
        model.add(Dense(self.units // 4, activation=self.activation))
        model.add(Dense(1, activation="sigmoid"))

        model.compile(optimizer=self.optimizer, loss=self.loss, metrics=self.metrics)

        return model

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the LSTM model.

        Args:
            X: Input features (shape: [samples, features] or [samples, timesteps, features])
            y: Target values
        """
        # Handle input shape
        if len(X.shape) == 2:
            # Create sequences for LSTM
            n_samples = X.shape[0]
            n_features = X.shape[1]
            n_sequences = n_samples - self.sequence_length + 1

            if n_sequences < 1:
                # Not enough samples for a sequence, adjust sequence length
                self.sequence_length = n_samples
                self.model = self._build_model()
                n_sequences = 1

            # Create sequences
            X_sequences = np.zeros((n_sequences, self.sequence_length, n_features))
            y_sequences = np.zeros(n_sequences)

            for i in range(n_sequences):
                X_sequences[i] = X[i : i + self.sequence_length]
                y_sequences[i] = y[i + self.sequence_length - 1]

            X_train = X_sequences
            y_train = y_sequences
        else:
            # Input is already in sequence form
            X_train = X
            y_train = y

        self.model.fit(
            X_train,
            y_train,
            epochs=self.epochs,
            batch_size=min(self.batch_size, len(y_train)),
            validation_split=0.2,
            verbose=0,
        )

        self.is_trained = True
        self.train_time = datetime.now().isoformat()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Generate predictions.

        Args:
            X: Input features (shape: [samples, features] or [samples, timesteps, features])

        Returns:
            Binary predictions
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        # Handle input shape
        if len(X.shape) == 2:
            # Create sequences for prediction
            n_samples = X.shape[0]
            n_features = X.shape[1]
            n_sequences = n_samples - self.sequence_length + 1

            if n_sequences < 1:
                # Not enough samples, pad with zeros
                pad_size = self.sequence_length - n_samples
                X = np.pad(X, ((0, pad_size), (0, 0)), mode="constant")
                n_samples = X.shape[0]
                n_sequences = 1

            # Create sequences
            X_sequences = np.zeros((n_sequences, self.sequence_length, n_features))
            for i in range(n_sequences):
                X_sequences[i] = X[i : i + self.sequence_length]

            X_pred = X_sequences
        else:
            # Input is already in sequence form
            X_pred = X

        # Get predictions
        predictions = self.model.predict(X_pred, verbose=0)

        # If input was 2D, we need to align predictions with input samples
        if len(X.shape) == 2:
            full_predictions = np.zeros(n_samples)
            full_predictions[self.sequence_length - 1 :] = predictions.flatten()
            return (full_predictions > 0.5).astype(int)
        else:
            return (predictions > 0.5).astype(int)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Generate probability predictions.

        Args:
            X: Input features (shape: [samples, features] or [samples, timesteps, features])

        Returns:
            Probability predictions
        """
        if not self.is_trained:
            raise RuntimeError("Model must be trained before prediction")

        # Handle input shape
        if len(X.shape) == 2:
            # Create sequences for prediction
            n_samples = X.shape[0]
            n_features = X.shape[1]
            n_sequences = n_samples - self.sequence_length + 1

            if n_sequences < 1:
                # Not enough samples, pad with zeros
                pad_size = self.sequence_length - n_samples
                X = np.pad(X, ((0, pad_size), (0, 0)), mode="constant")
                n_samples = X.shape[0]
                n_sequences = 1

            # Create sequences
            X_sequences = np.zeros((n_sequences, self.sequence_length, n_features))
            for i in range(n_sequences):
                X_sequences[i] = X[i : i + self.sequence_length]

            X_pred = X_sequences
        else:
            # Input is already in sequence form
            X_pred = X

        # Get predictions
        predictions = self.model.predict(X_pred, verbose=0)

        # If input was 2D, we need to align predictions with input samples
        if len(X.shape) == 2:
            full_predictions = np.full(n_samples, 0.5)
            full_predictions[self.sequence_length - 1 :] = predictions.flatten()
            return full_predictions
        else:
            return predictions
