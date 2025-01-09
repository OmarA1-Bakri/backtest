"""Alpha Vantage data provider implementation."""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Union
import pandas as pd
import aiohttp
from core.config.settings import settings
from data.providers.base import DataProvider


class AlphaVantageProvider(DataProvider):
    """Alpha Vantage API data provider."""

    BASE_URL = "https://www.alphavantage.co/query"
    API_KEY = settings.ALPHA_VANTAGE_API_KEY

    def __init__(self):
        """Initialize the provider."""
        self._session = None
        self._rate_limit_delay = 12.1  # Alpha Vantage free tier: 5 calls per minute

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(self, params: Dict) -> Dict:
        """Make an API request with rate limiting."""
        params["apikey"] = self.API_KEY
        session = await self._get_session()

        async with session.get(self.BASE_URL, params=params) as response:
            data = await response.json()
            if "Error Message" in data:
                raise ValueError(f"Alpha Vantage API error: {data['Error Message']}")
            await asyncio.sleep(self._rate_limit_delay)
            return data

    async def get_stock_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get stock data for a given symbol and date range."""
        function = "TIME_SERIES_DAILY" if interval == "1d" else "TIME_SERIES_INTRADAY"
        params = {
            "function": function,
            "symbol": symbol,
            "outputsize": "full",
        }

        if interval != "1d":
            params["interval"] = interval

        data = await self._make_request(params)
        time_series_key = (
            "Time Series (Daily)"
            if interval == "1d"
            else f'Time Series ({interval.replace("m", " min")})'
        )

        df = pd.DataFrame.from_dict(data[time_series_key], orient="index")
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()

        # Convert columns to numeric
        for col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(r"[^\d.]", ""))

        # Rename columns
        df.columns = ["Open", "High", "Low", "Close", "Volume"]

        # Filter by date range
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        return df.loc[start_date:end_date]

    async def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple stocks."""
        tasks = [
            self.get_stock_data(symbol, start_date, end_date, interval)
            for symbol in symbols
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            symbol: df
            for symbol, df in zip(symbols, results)
            if not isinstance(df, Exception)
        }

    async def get_latest_price(self, symbol: str) -> float:
        """Get the latest price for a symbol."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
        }
        data = await self._make_request(params)
        return float(data["Global Quote"]["05. price"])

    async def get_company_info(self, symbol: str) -> Dict:
        """Get company information."""
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
        }
        return await self._make_request(params)

    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
