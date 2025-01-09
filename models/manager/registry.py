from typing import Dict, Type, Optional, List, Any
from base.model import BaseModel
import logging

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry for model classes and configurations."""

    def __init__(self):
        """Initialize model registry."""
        self._models: Dict[str, Type[BaseModel]] = {}
        self._configs: Dict[str, Dict[str, Any]] = {}

    def register(
        self,
        name: str,
        model_class: Type[BaseModel],
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register a model class.

        Args:
            name: Model identifier
            model_class: Model class to register
            config: Optional model configuration
        """
        if name in self._models:
            logger.warning(f"Overwriting existing model registration: {name}")

        if not issubclass(model_class, BaseModel):
            raise TypeError(f"Model class must inherit from BaseModel: {model_class}")

        self._models[name] = model_class
        self._configs[name] = config or {}

    def unregister(self, name: str) -> None:
        """Unregister a model class.

        Args:
            name: Model identifier to unregister
        """
        if name in self._models:
            del self._models[name]
            del self._configs[name]

    def get_class(self, name: str) -> Type[BaseModel]:
        """Get a registered model class.

        Args:
            name: Model identifier

        Returns:
            Registered model class
        """
        if name not in self._models:
            raise KeyError(f"Model not registered: {name}")

        return self._models[name]

    def get_config(self, name: str) -> Dict[str, Any]:
        """Get a model's configuration.

        Args:
            name: Model identifier

        Returns:
            Model configuration dictionary
        """
        if name not in self._configs:
            raise KeyError(f"Model not registered: {name}")

        return self._configs[name].copy()

    def create_instance(
        self,
        name: str,
        features: List[str],
        override_config: Optional[Dict[str, Any]] = None,
    ) -> BaseModel:
        """Create a model instance.

        Args:
            name: Model identifier
            features: Feature list for the model
            override_config: Optional configuration override

        Returns:
            Model instance
        """
        model_class = self.get_class(name)
        config = self.get_config(name)

        if override_config:
            config.update(override_config)

        return model_class(name=name, features=features, model_params=config)

    def list_models(self) -> List[str]:
        """List registered model names.

        Returns:
            List of registered model names
        """
        return list(self._models.keys())

    def get_info(self, name: str) -> Dict[str, Any]:
        """Get information about a registered model.

        Args:
            name: Model identifier

        Returns:
            Dictionary with model information
        """
        if name not in self._models:
            raise KeyError(f"Model not registered: {name}")

        model_class = self._models[name]
        return {
            "name": name,
            "class": model_class.__name__,
            "module": model_class.__module__,
            "config": self.get_config(name),
            "doc": model_class.__doc__,
        }

    def clear(self) -> None:
        """Clear all registrations."""
        self._models.clear()
        self._configs.clear()
