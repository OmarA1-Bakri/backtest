from typing import Dict, Any, Optional, List, Union, Callable
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from ..sources.base import DataSource

logger = logging.getLogger(__name__)


class DataPipeline:
    """Data processing pipeline."""

    def __init__(self, source: DataSource, config: Optional[Dict[str, Any]] = None):
        """Initialize data pipeline.

        Args:
            source: Data source
            config: Pipeline configuration
        """
        self.source = source
        self.config = config or {}
        self.transformers = []
        self.features = []
        self.metadata = {}

    def add_transformer(
        self, func: Callable[[pd.DataFrame], pd.DataFrame], name: Optional[str] = None
    ) -> None:
        """Add a data transformation function.

        Args:
            func: Transformation function
            name: Transformer name
        """
        name = name or func.__name__
        self.transformers.append((name, func))

    def add_feature(
        self, func: Callable[[pd.DataFrame], pd.Series], name: Optional[str] = None
    ) -> None:
        """Add a feature generation function.

        Args:
            func: Feature function
            name: Feature name
        """
        name = name or func.__name__
        self.features.append((name, func))

    def process(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """Process data through pipeline.

        Args:
            symbol: Asset symbol
            start_date: Start date
            end_date: End date
            **kwargs: Additional parameters

        Returns:
            Processed DataFrame
        """
        # Load data
        data = self.source.load(symbol, start_date, end_date, **kwargs)

        # Validate raw data
        if not self.source.validate(data):
            raise ValueError("Invalid data from source")

        # Apply transformations
        for name, func in self.transformers:
            try:
                logger.debug(f"Applying transformer: {name}")
                data = func(data)
            except Exception as e:
                logger.error(f"Error in transformer {name}: {e}")
                raise

        # Generate features
        for name, func in self.features:
            try:
                logger.debug(f"Generating feature: {name}")
                data[name] = func(data)
            except Exception as e:
                logger.error(f"Error in feature {name}: {e}")
                raise

        # Update metadata
        self.metadata.update(
            {
                "symbol": symbol,
                "start_date": data["date"].min(),
                "end_date": data["date"].max(),
                "rows": len(data),
                "columns": list(data.columns),
                "transformers": [name for name, _ in self.transformers],
                "features": [name for name, _ in self.features],
                "source_metadata": self.source.get_metadata(),
            }
        )

        return data

    def get_metadata(self) -> Dict[str, Any]:
        """Get pipeline metadata.

        Returns:
            Dictionary of metadata
        """
        return self.metadata.copy()

    def clear(self) -> None:
        """Clear pipeline transformers and features."""
        self.transformers.clear()
        self.features.clear()
        self.metadata.clear()
        logger.info("Pipeline cleared")

    @staticmethod
    def create_standard_pipeline(
        source: DataSource, config: Optional[Dict[str, Any]] = None
    ) -> "DataPipeline":
        """Create pipeline with standard transformations.

        Args:
            source: Data source
            config: Pipeline configuration

        Returns:
            Configured pipeline
        """
        pipeline = DataPipeline(source, config)

        # Add standard transformers
        pipeline.add_transformer(lambda df: df.sort_values("date"), "sort_dates")
        pipeline.add_transformer(lambda df: df.dropna(), "remove_missing")

        # Add standard features
        pipeline.add_feature(lambda df: df["close"].pct_change(), "returns")
        pipeline.add_feature(
            lambda df: df["returns"].rolling(window=20).std(), "volatility_20d"
        )
        pipeline.add_feature(lambda df: df["close"].rolling(window=20).mean(), "sma_20")
        pipeline.add_feature(lambda df: df["close"].rolling(window=50).mean(), "sma_50")

        return pipeline
