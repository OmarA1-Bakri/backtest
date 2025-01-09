# backtest/models/random_forest_model.py

from sklearn.ensemble import RandomForestRegressor
import joblib
import os
from logger import logger


class RandomForestModel:
    def __init__(self, features, model_dir="models/"):
        self.features = features
        self.model_dir = (
            model_dir if isinstance(model_dir, str) else model_dir.model_dir
        )
        self.model_path = os.path.join(self.model_dir, "random_forest_model.joblib")
        os.makedirs(self.model_dir, exist_ok=True)
        self.model = RandomForestRegressor(
            n_estimators=100, random_state=42, min_samples_split=5, min_samples_leaf=2
        )
        logger.info(f"RandomForestModel initialized with model path: {self.model_path}")

    def train(self, X, y):
        try:
            logger.info("Starting training of Random Forest model.")
            self.model.fit(X, y)
            logger.info("Random Forest model trained successfully.")
        except Exception as e:
            logger.error(f"Error training Random Forest model: {e}")
            raise

    def predict(self, X):
        try:
            if self.model is None:
                raise ValueError("Random Forest model is not trained.")
            logger.info("Starting prediction with Random Forest model.")
            predictions = self.model.predict(X)
            logger.info("Prediction with Random Forest model completed.")
            return predictions
        except Exception as e:
            logger.error(f"Error predicting with Random Forest model: {e}")
            raise

    def save_model(self):
        try:
            if self.model is None:
                raise ValueError("No Random Forest model to save.")
            joblib.dump(self.model, self.model_path)
            logger.info(f"Random Forest model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving Random Forest model: {e}")
            raise

    def load_model(self):
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"Random Forest model file not found at {self.model_path}"
                )
            self.model = joblib.load(self.model_path)
            logger.info(f"Random Forest model loaded from {self.model_path}")
        except FileNotFoundError as fnf_error:
            logger.error(fnf_error)
            raise
        except Exception as e:
            logger.error(f"Error loading Random Forest model: {e}")
            raise
