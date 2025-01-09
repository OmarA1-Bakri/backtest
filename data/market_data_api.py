"""Service for fetching market data from API providers."""

from typing import Dict, List, Optional, Union
from datetime import datetime
import pandas as pd
import asyncio
import logging
from data.providers.factory import DataProviderFactory, ProviderType
from core.config.settings import settings

logger = logging.getLogger(__name__)


class MarketDataAPIService:
    """Service for fetching market data from various API providers."""

    def __init__(self, default_provider: ProviderType = ProviderType.POLYGON):
        """Initialize the market data API service.

        Args:
            default_provider: Default data provider to use
        """
        self.default_provider = default_provider
        self._provider_factory = DataProviderFactory()

    async def get_historical_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
        provider: Optional[ProviderType] = None,
    ) -> pd.DataFrame:
        """Fetch historical market data for a symbol.

        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '5m', etc.)
            provider: Specific provider to use, otherwise uses default

        Returns:
            DataFrame with OHLCV data
        """
        try:
            provider = provider or self.default_provider
            data_provider = self._provider_factory.get_provider(provider)

            df = await data_provider.get_stock_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
            )

            return df

        except Exception as e:
            logger.error(f"Error fetching data for {symbol} from {provider}: {str(e)}")
            # Try fallback provider if primary fails
            if provider != ProviderType.ALPHA_VANTAGE:
                logger.info(f"Attempting fallback to Alpha Vantage for {symbol}")
                return await self.get_historical_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=ProviderType.ALPHA_VANTAGE,
                )
            raise

    async def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
        provider: Optional[ProviderType] = None,
    ) -> Dict[str, pd.DataFrame]:
        """Fetch historical data for multiple stocks.

        Args:
            symbols: List of trading symbols
            start_date: Start date for historical data
            end_date: End date for historical data
            interval: Data interval ('1d', '5m', etc.)
            provider: Specific provider to use, otherwise uses default

        Returns:
            Dict mapping symbols to their respective DataFrames
        """
        provider = provider or self.default_provider
        data_provider = self._provider_factory.get_provider(provider)

        try:
            return await data_provider.get_multiple_stocks(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
            )
        except Exception as e:
            logger.error(f"Error fetching multiple stocks from {provider}: {str(e)}")
            if provider != ProviderType.ALPHA_VANTAGE:
                logger.info(f"Attempting fallback to Alpha Vantage for multiple stocks")
                return await self.get_multiple_stocks(
                    symbols=symbols,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                    provider=ProviderType.ALPHA_VANTAGE,
                )
            raise

    async def get_latest_prices(
        self,
        symbols: List[str],
        provider: Optional[ProviderType] = None,
    ) -> Dict[str, float]:
        """Get latest prices for multiple symbols.

        Args:
            symbols: List of trading symbols
            provider: Specific provider to use, otherwise uses default

        Returns:
            Dict mapping symbols to their latest prices
        """
        provider = provider or self.default_provider
        data_provider = self._provider_factory.get_provider(provider)

        tasks = [data_provider.get_latest_price(symbol) for symbol in symbols]
        prices = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            symbol: price
            for symbol, price in zip(symbols, prices)
            if not isinstance(price, Exception)
        }

    async def get_company_info(
        self,
        symbol: str,
        provider: Optional[ProviderType] = None,
    ) -> Dict:
        """Get company information for a symbol.

        Args:
            symbol: Trading symbol
            provider: Specific provider to use, otherwise uses default

        Returns:
            Dict containing company information
        """
        provider = provider or self.default_provider
        data_provider = self._provider_factory.get_provider(provider)

        try:
            return await data_provider.get_company_info(symbol)
        except Exception as e:
            logger.error(
                f"Error fetching company info for {symbol} from {provider}: {str(e)}"
            )
            if provider != ProviderType.ALPHA_VANTAGE:
                return await self.get_company_info(
                    symbol=symbol,
                    provider=ProviderType.ALPHA_VANTAGE,
                )
            raise

    async def close(self):
        """Close all provider connections."""
        await self._provider_factory.close_all()
