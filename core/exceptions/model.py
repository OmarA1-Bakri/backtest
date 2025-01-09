"""Model-specific exceptions for the BackTest AI application."""

from typing import Any, Dict, Optional

from core.exceptions.base import BackTestError


class ModelError(BackTestError):
    """Base exception for model-related errors."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ModelError.

        Args:
            message: Error message
            model: Optional name of the model
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if model:
            error_details["model"] = model

        super().__init__(
            message=message,
            error_code="MODEL_ERROR",
            details=error_details,
        )


class DataLeakageError(ModelError):
    """Exception raised when data leakage is detected."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        feature: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize DataLeakageError.

        Args:
            message: Error message
            model: Optional name of the model
            feature: Optional name of the feature causing leakage
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if feature:
            error_details["feature"] = feature

        super().__init__(
            message=message,
            model=model,
            details=error_details,
        )
        self.error_code = "DATA_LEAKAGE_ERROR"


class PredictionError(ModelError):
    """Exception raised when prediction fails."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        input_shape: Optional[tuple] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize PredictionError.

        Args:
            message: Error message
            model: Optional name of the model
            input_shape: Optional shape of the input data
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if input_shape:
            error_details["input_shape"] = input_shape

        super().__init__(
            message=message,
            model=model,
            details=error_details,
        )
        self.error_code = "PREDICTION_ERROR"


class ModelNotFoundError(ModelError):
    """Exception raised when a model is not found."""

    def __init__(
        self,
        message: str,
        model: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ModelNotFoundError.

        Args:
            message: Error message
            model: Name of the model that was not found
            details: Optional dictionary containing additional error details
        """
        super().__init__(
            message=message,
            model=model,
            details=details,
        )
        self.error_code = "MODEL_NOT_FOUND_ERROR"


class ModelTrainingError(ModelError):
    """Exception raised when model training fails."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        epoch: Optional[int] = None,
        metrics: Optional[Dict[str, float]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ModelTrainingError.

        Args:
            message: Error message
            model: Optional name of the model
            epoch: Optional epoch number where training failed
            metrics: Optional dictionary of training metrics
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if epoch is not None:
            error_details["epoch"] = epoch
        if metrics:
            error_details["metrics"] = metrics

        super().__init__(
            message=message,
            model=model,
            details=error_details,
        )
        self.error_code = "MODEL_TRAINING_ERROR"


class ModelValidationError(ModelError):
    """Exception raised when model validation fails."""

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        validation_metrics: Optional[Dict[str, float]] = None,
        threshold_metrics: Optional[Dict[str, float]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize ModelValidationError.

        Args:
            message: Error message
            model: Optional name of the model
            validation_metrics: Optional dictionary of validation metrics
            threshold_metrics: Optional dictionary of threshold metrics
            details: Optional dictionary containing additional error details
        """
        error_details = details or {}
        if validation_metrics:
            error_details["validation_metrics"] = validation_metrics
        if threshold_metrics:
            error_details["threshold_metrics"] = threshold_metrics

        super().__init__(
            message=message,
            model=model,
            details=error_details,
        )
        self.error_code = "MODEL_VALIDATION_ERROR"
