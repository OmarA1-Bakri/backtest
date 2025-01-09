"""Model configuration."""

from typing import Dict, Any

# LSTM model configuration
LSTM_CONFIG: Dict[str, Any] = {
    "hidden_units": [50, 25],
    "time_steps": 50,
    "dropout_rate": 0.2,
    "l2_reg": 0.01,
    "dense_units": 25,
    "epochs": 50,
    "batch_size": 32,
    "validation_split": 0.2,
    "patience": 10,
}

# XGBoost model configuration
XGBOOST_CONFIG: Dict[str, Any] = {
    "max_depth": 3,
    "learning_rate": 0.1,
    "n_estimators": 100,
    "objective": "binary:logistic",
    "eval_metric": "logloss",
    "early_stopping_rounds": 10,
}

# Model configurations
MODEL_CONFIGS = {
    "time_steps": 10,  # Default time steps for sequence models
    "lstm": {
        "input_dim": None,  # Will be set based on features
        "hidden_dim": 50,
        "num_layers": 2,
        "dropout_rate": 0.2,
        "batch_size": 32,
        "epochs": 50,
        "learning_rate": 0.001,
        "dense_units": 25,
        "optimizer": "adam",
        "loss": "mse",
        "metrics": ["mae"],
    },
    "xgboost": {
        "max_depth": 3,
        "learning_rate": 0.1,
        "n_estimators": 100,
        "objective": "reg:squarederror",
        "booster": "gbtree",
        "tree_method": "auto",
        "n_jobs": -1,
        "gamma": 0,
        "min_child_weight": 1,
        "max_delta_step": 0,
        "subsample": 1,
        "colsample_bytree": 1,
        "colsample_bylevel": 1,
        "colsample_bynode": 1,
        "reg_alpha": 0,
        "reg_lambda": 1,
        "scale_pos_weight": 1,
        "base_score": 0.5,
        "random_state": 42,
        "missing": None,
        "num_parallel_tree": 1,
        "monotone_constraints": None,
        "interaction_constraints": None,
        "importance_type": "gain",
        "eval_metric": "logloss",
        "early_stopping_rounds": 10,
    },
}
