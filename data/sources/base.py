from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataSource(ABC):
    """Abstract base class for data sources."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize data source.

        Args:
            name: Source identifier
            config: Source configuration
        """
        self.name = name
        self.config = config or {}
        self.metadata = {}

    @abstractmethod
    def load(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """Load data from source.

        Args:
            symbol: Asset symbol
            start_date: Start date for data
            end_date: End date for data
            **kwargs: Additional source-specific parameters

        Returns:
            DataFrame with market data
        """
        pass

    @abstractmethod
    def validate(self, data: pd.DataFrame) -> bool:
        """Validate loaded data.

        Args:
            data: DataFrame to validate

        Returns:
            True if data is valid
        """
        pass

    def get_metadata(self) -> Dict[str, Any]:
        """Get source metadata.

        Returns:
            Dictionary of metadata
        """
        return self.metadata.copy()

    def update_metadata(self, **kwargs) -> None:
        """Update source metadata.

        Args:
            **kwargs: Metadata key-value pairs
        """
        self.metadata.update(kwargs)
