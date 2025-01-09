"""Factory for creating data providers."""

from enum import Enum
from typing import Optional
from data.providers.base import DataProvider
from data.providers.alpha_vantage import AlphaVantageProvider
from data.providers.polygon import PolygonProvider


class ProviderType(str, Enum):
    """Available data provider types."""

    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"


class DataProviderFactory:
    """Factory for creating and managing data providers."""

    _instances: dict[str, DataProvider] = {}

    @classmethod
    def get_provider(cls, provider_type: ProviderType) -> DataProvider:
        """Get or create a data provider instance."""
        if provider_type not in cls._instances:
            if provider_type == ProviderType.ALPHA_VANTAGE:
                cls._instances[provider_type] = AlphaVantageProvider()
            elif provider_type == ProviderType.POLYGON:
                cls._instances[provider_type] = PolygonProvider()
            else:
                raise ValueError(f"Unknown provider type: {provider_type}")
        return cls._instances[provider_type]

    @classmethod
    async def close_all(cls):
        """Close all provider instances."""
        for provider in cls._instances.values():
            await provider.close()
        cls._instances.clear()
