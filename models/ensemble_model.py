from sklearn.ensemble import StackingRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_predict
from sklearn.metrics import roc_auc_score
from xgboost_model import XGBoostModel
from lstm_model import LSTMModel
from hmm_model import HMMModel
from random_forest_model import RandomForestModel
from logger import logger
import numpy as np
import joblib
import os


class EnsembleModel:
    def __init__(self, features, model_settings):
        self.features = features
        self.model_settings = model_settings
        self.xgb_model = XGBoostModel(
            features=features, model_dir=model_settings.model_dir
        )
        self.lstm_model = LSTMModel(
            time_steps=model_settings.time_steps,
            n_features=len(features),
            model_dir=model_settings.model_dir,
        )
        self.hmm_model = HMMModel(
            n_components=model_settings.n_components, model_dir=model_settings.model_dir
        )
        self.rf_model = RandomForestModel(
            features=features, model_dir=model_settings.model_dir
        )

        estimators = [
            ("xgb", self.xgb_model),
            ("lstm", self.lstm_model),
            ("rf", self.rf_model),
        ]

        meta_model = XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42)

        self.ensemble = StackingRegressor(
            estimators=estimators, final_estimator=meta_model, cv=5, n_jobs=-1
        )

    def fit(self, X, y):
        try:
            X_lstm = X.reshape(
                -1, self.lstm_model.time_steps, self.lstm_model.n_features
            )
            self.xgb_model.train(X, y)
            self.lstm_model.train(X_lstm, y)
            self.rf_model.train(X, y)
            self.hmm_model.train(X)

            xgb_preds = cross_val_predict(
                self.xgb_model, X, y, cv=5, method="predict_proba"
            )[:, 1]
            lstm_preds = cross_val_predict(self.lstm_model, X_lstm, y, cv=5)
            rf_preds = cross_val_predict(self.rf_model, X, y, cv=5)
            hmm_preds = self.hmm_model.predict(X)

            meta_features = np.column_stack(
                (xgb_preds, lstm_preds, rf_preds, hmm_preds)
            )

            self.ensemble.fit(meta_features, y)

            logger.info("Ensemble model fitted successfully")
        except Exception as e:
            logger.error(f"Error fitting ensemble model: {e}")
            raise

    def predict(self, X):
        try:
            X_lstm = X.reshape(
                -1, self.lstm_model.time_steps, self.lstm_model.n_features
            )
            xgb_preds = self.xgb_model.predict_proba(X)[:, 1]
            lstm_preds = self.lstm_model.predict(X_lstm)
            rf_preds = self.rf_model.predict(X)
            hmm_preds = self.hmm_model.predict(X)

            meta_features = np.column_stack(
                (xgb_preds, lstm_preds, rf_preds, hmm_preds)
            )
            ensemble_pred = self.ensemble.predict(meta_features)

            return ensemble_pred
        except Exception as e:
            logger.error(f"Error predicting with ensemble model: {e}")
            raise

    def save_model(self, model_dir):
        try:
            self.xgb_model.save_model()
            self.lstm_model.save_model()
            self.rf_model.save_model()
            self.hmm_model.save_model()
            joblib.dump(
                self.ensemble, os.path.join(model_dir, "stacking_ensemble.joblib")
            )
            logger.info("Ensemble model components saved successfully")
        except Exception as e:
            logger.error(f"Error saving ensemble model components: {e}")
            raise

    def load_model(self, model_dir):
        try:
            self.xgb_model.load_model()
            self.lstm_model.load_model()
            self.rf_model.load_model()
            self.hmm_model.load_model()
            self.ensemble = joblib.load(
                os.path.join(model_dir, "stacking_ensemble.joblib")
            )
            logger.info("Ensemble model components loaded successfully")
        except Exception as e:
            logger.error(f"Error loading ensemble model components: {e}")
            raise

    def evaluate(self, X, y):
        try:
            predictions = self.predict(X)
            auc_score = roc_auc_score(y, predictions)
            logger.info(f"Ensemble model AUC score: {auc_score:.4f}")
            return auc_score
        except Exception as e:
            logger.error(f"Error evaluating ensemble model: {e}")
            raise
