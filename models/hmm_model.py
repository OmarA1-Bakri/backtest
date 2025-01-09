from pomegranate.distributions import Normal
from pomegranate.hmm import DenseHMM
import joblib
import numpy as np
from logger import logger
import os


class HMMModel:
    def __init__(self, n_components=3, model_dir="models/"):
        self.n_components = n_components
        self.model = None
        self.model_dir = (
            model_dir if isinstance(model_dir, str) else model_dir.model_dir
        )
        self.model_path = os.path.join(self.model_dir, "hmm_model.joblib")
        os.makedirs(self.model_dir, exist_ok=True)
        self.state_interpretation = {}

    def train(self, X_train):
        try:
            # Ensure X_train is a list of sequences
            if not isinstance(X_train, list):
                X_train = [X_train]
            X_train = [np.atleast_2d(sequence) for sequence in X_train]
            # Initialize HMM with multivariate normal distributions
            distributions = [Normal() for _ in range(self.n_components)]
            self.model = DenseHMM(distributions=distributions)
            # Fit the model
            self.model.fit(X_train)
            logger.info("HMM model trained with pomegranate")
        except Exception as e:
            logger.error(f"Error training HMM: {str(e)}")
            raise

    def predict(self, X):
        if not self.model:
            logger.warning("HMM model is not trained.")
            return []
        try:
            return self.model.predict(X)
        except Exception as e:
            logger.error(f"Error predicting with HMM: {str(e)}")
            return []

    def predict_proba(self, X):
        if not self.model:
            logger.warning("HMM model is not trained.")
            return []
        try:
            return self.model.predict_proba(X)
        except Exception as e:
            logger.error(f"Error predicting probabilities with HMM: {str(e)}")
            return []

    def get_most_likely_state_sequence(self, X):
        if not self.model:
            logger.warning("HMM model is not trained.")
            return []
        try:
            return self.model.viterbi(X)
        except Exception as e:
            logger.error(f"Error getting most likely state sequence: {str(e)}")
            return []

    def save_model(self):
        try:
            joblib.dump(self.model, self.model_path)
            logger.info(f"HMM model saved to {self.model_path}")
        except Exception as e:
            logger.error(f"Error saving HMM model: {str(e)}")
            raise

    def load_model(self):
        try:
            self.model = joblib.load(self.model_path)
            logger.info(f"HMM model loaded from {self.model_path}")
            self.interpret_states()
        except FileNotFoundError:
            logger.warning(f"HMM model file not found at {self.model_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading HMM model: {str(e)}")
            raise

    def interpret_states(self):
        try:
            state_characteristics = {}
            for i, state in enumerate(self.model.distributions):
                mean = state.parameters[0]
                std = state.parameters[1]
                state_characteristics[f"State_{i}"] = {"mean": mean, "std": std}

            sorted_states = sorted(
                state_characteristics.items(), key=lambda x: x[1]["std"]
            )
            for i, (state, params) in enumerate(sorted_states):
                if i == 0:
                    regime = "Low Volatility"
                elif i == 1:
                    regime = "Medium Volatility"
                else:
                    regime = "High Volatility"
                state_characteristics[state]["regime"] = regime
            self.state_interpretation = state_characteristics
            logger.info(f"State interpretations: {self.state_interpretation}")
        except Exception as e:
            logger.error(f"Error interpreting HMM states: {str(e)}")
