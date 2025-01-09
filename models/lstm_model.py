"""LSTM model implementation."""

from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers, regularizers


class LSTMModel:
    """LSTM model for time series prediction."""

    def __init__(
        self,
        name: str,
        features: List[str],
        model_params: Dict[str, Any],
        model_path: Path,
    ):
        """Initialize LSTM model.

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
        self.time_steps = model_params.get("time_steps", 10)
        self.hidden_units = model_params.get("hidden_units", [50, 50])
        self.dense_units = model_params.get("dense_units", 25)
        self.dropout_rate = model_params.get("dropout_rate", 0.2)
        self.l2_reg = model_params.get("l2_reg", 0.01)
        self.learning_rate = model_params.get("learning_rate", 0.001)
        self.batch_size = model_params.get("batch_size", 32)
        self.epochs = model_params.get("epochs", 50)

        # Build model
        self.model = self._build_model()

    def _build_model(self) -> tf.keras.Model:
        """Build LSTM model architecture.

        Returns:
            Built model
        """
        model = models.Sequential()

        # Input layer
        model.add(
            layers.LSTM(
                self.hidden_units[0],
                input_shape=(self.time_steps, len(self.features)),
                return_sequences=True,
                kernel_regularizer=regularizers.l2(self.l2_reg),
            )
        )
        model.add(layers.Dropout(self.dropout_rate))

        # Hidden LSTM layers
        for units in self.hidden_units[1:]:
            model.add(
                layers.LSTM(
                    units,
                    return_sequences=True,
                    kernel_regularizer=regularizers.l2(self.l2_reg),
                )
            )
            model.add(layers.Dropout(self.dropout_rate))

        # Dense layers
        model.add(layers.Dense(self.dense_units, activation="relu"))
        model.add(layers.Dropout(self.dropout_rate))
        model.add(layers.Dense(1))

        # Compile model
        model.compile(
            optimizer=optimizers.Adam(learning_rate=self.learning_rate),
            loss="mse",
            metrics=["mae"],
        )

        return model

    def train(self, X_train: np.ndarray, y_train: np.ndarray) -> None:
        """Train the model.

        Args:
            X_train: Training features
            y_train: Training labels
        """
        # Reshape input to (samples, time_steps, features)
        X_train = X_train.reshape(-1, self.time_steps, len(self.features))

        # Train model
        self.model.fit(
            X_train,
            y_train,
            batch_size=self.batch_size,
            epochs=self.epochs,
            validation_split=0.2,
            verbose=1,
        )

        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.save(self.model_path)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions.

        Args:
            X: Input features

        Returns:
            Predictions
        """
        # Reshape input to (samples, time_steps, features)
        X = X.reshape(-1, self.time_steps, len(self.features))
        return self.model.predict(X)
