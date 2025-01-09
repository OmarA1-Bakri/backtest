"""Market data downloader that combines API fetching with local caching."""

from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta
import pandas as pd
import asyncio
import logging
from pathlib import Path
from data.market_data_api import MarketDataAPIService
from data.providers.factory import ProviderType
from data.exporter import DataExporter, ExportFormat

logger = logging.getLogger(__name__)


class MarketDataDownloader:
    """Downloads and caches market data from various providers."""

    def __init__(
        self,
        cache_dir: Union[str, Path],
        export_format: ExportFormat = ExportFormat.PARQUET,
        default_provider: ProviderType = ProviderType.POLYGON,
        update_interval: timedelta = timedelta(days=1),
    ):
        """Initialize the market data downloader.

        Args:
            cache_dir: Directory for cached data files
            export_format: Format to save data in
            default_provider: Default data provider to use
            update_interval: How often to update cached data
        """
        self.cache_dir = Path(cache_dir)
        self.export_format = export_format
        self.update_interval = update_interval

        # Initialize services
        self.api_service = MarketDataAPIService(default_provider=default_provider)
        self.exporter = DataExporter(
            export_dir=self.cache_dir,
            format=export_format,
            partition_cols=["symbol", "interval"],
        )

        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
        force_download: bool = False,
    ) -> pd.DataFrame:
        """Get historical market data, using cache when possible.

        Args:
            symbol: Trading symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '5m', etc.)
            force_download: If True, bypass cache and download fresh data

        Returns:
            DataFrame with OHLCV data
        """
        # Convert dates if needed
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        # Check cache first
        if not force_download:
            cached_data = self._get_cached_data(symbol, interval)
            if cached_data is not None:
                cached_start = cached_data.index.min()
                cached_end = cached_data.index.max()

                # If cache covers our date range and is fresh enough
                if (
                    cached_start <= start_date
                    and cached_end >= end_date
                    and datetime.now() - cached_end <= self.update_interval
                ):
                    return cached_data.loc[start_date:end_date]

        # Download fresh data
        logger.info(f"Downloading fresh data for {symbol}")
        df = await self.api_service.get_historical_data(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            interval=interval,
        )

        # Cache the data
        if not df.empty:
            metadata = {
                "symbol": symbol,
                "interval": interval,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }
            self.exporter.export_data(
                df=df,
                name=f"market_data_{symbol}_{interval}",
                metadata=metadata,
            )

        return df

    async def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
        force_download: bool = False,
    ) -> Dict[str, pd.DataFrame]:
        """Get historical data for multiple stocks, using cache when possible.

        Args:
            symbols: List of trading symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '5m', etc.)
            force_download: If True, bypass cache and download fresh data

        Returns:
            Dict mapping symbols to their respective DataFrames
        """
        tasks = [
            self.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                force_download=force_download,
            )
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            symbol: df
            for symbol, df in zip(symbols, results)
            if not isinstance(df, Exception) and not df.empty
        }

    def _get_cached_data(
        self,
        symbol: str,
        interval: str,
    ) -> Optional[pd.DataFrame]:
        """Attempt to load cached data for a symbol.

        Args:
            symbol: Trading symbol
            interval: Data interval

        Returns:
            DataFrame if cache exists and is valid, None otherwise
        """
        # Find latest cache file for symbol
        pattern = f"market_data_{symbol}_{interval}_*.{self.export_format}"
        cache_files = list(self.cache_dir.glob(pattern))

        if not cache_files:
            return None

        # Get most recent cache file
        latest_cache = max(cache_files, key=lambda p: p.stat().st_mtime)

        try:
            if self.export_format == ExportFormat.PARQUET:
                return pd.read_parquet(latest_cache)
            elif self.export_format == ExportFormat.FEATHER:
                return pd.read_feather(latest_cache)
            elif self.export_format == ExportFormat.CSV:
                return pd.read_csv(
                    latest_cache,
                    index_col=0,
                    parse_dates=True,
                )
            else:  # JSON or PICKLE
                return pd.read_pickle(latest_cache)

        except Exception as e:
            logger.error(f"Error reading cache file {latest_cache}: {str(e)}")
            return None

    async def update_cache(
        self,
        symbols: List[str],
        days_of_history: int = 365,
        intervals: List[str] = ["1d"],
    ):
        """Update cache for specified symbols and intervals.

        Args:
            symbols: List of symbols to update
            days_of_history: Number of days of historical data to cache
            intervals: List of intervals to cache
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_of_history)

        for interval in intervals:
            await self.get_multiple_stocks(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
                force_download=True,
            )

    async def close(self):
        """Close all connections."""
        await self.api_service.close()
