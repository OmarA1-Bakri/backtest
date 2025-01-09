"""Polygon.io data provider implementation."""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union
import pandas as pd
import aiohttp
from core.config.settings import settings
from data.providers.base import DataProvider


class PolygonProvider(DataProvider):
    """Polygon.io API data provider."""

    BASE_URL = "https://api.polygon.io"
    API_KEY = settings.POLYGON_API_KEY

    def __init__(self):
        """Initialize the provider."""
        self._session = None
        self._rate_limit_delay = 0.2  # Polygon.io rate limit: 5 requests per second

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an API request with rate limiting."""
        if params is None:
            params = {}
        params["apiKey"] = self.API_KEY

        session = await self._get_session()
        url = f"{self.BASE_URL}{endpoint}"

        async with session.get(url, params=params) as response:
            data = await response.json()
            if "error" in data:
                raise ValueError(f"Polygon.io API error: {data['error']}")
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
        # Convert dates to expected format
        if isinstance(start_date, str):
            start_date = pd.to_datetime(start_date)
        if isinstance(end_date, str):
            end_date = pd.to_datetime(end_date)

        # Convert interval to Polygon.io format
        interval_map = {
            "1m": "minute",
            "5m": "minute",
            "15m": "minute",
            "30m": "minute",
            "1h": "hour",
            "1d": "day",
        }
        timespan = interval_map.get(interval, "day")
        multiplier = interval[0] if interval != "1d" else "1"

        # Fetch data in chunks to handle API limits
        all_results = []
        current_date = start_date
        while current_date <= end_date:
            next_date = min(current_date + timedelta(days=365), end_date)
            endpoint = f"/v2/aggs/ticker/{symbol}/range/{multiplier}/{timespan}/{current_date.strftime('%Y-%m-%d')}/{next_date.strftime('%Y-%m-%d')}"

            data = await self._make_request(endpoint)
            if data.get("results"):
                all_results.extend(data["results"])

            current_date = next_date + timedelta(days=1)

        if not all_results:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(all_results)
        df.columns = ["Open", "High", "Low", "Close", "Volume", "VWAP", "Timestamp"]
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
        df.set_index("Timestamp", inplace=True)
        df.sort_index(inplace=True)

        return df

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
        endpoint = f"/v2/last/trade/{symbol}"
        data = await self._make_request(endpoint)
        return float(data["results"]["p"])

    async def get_company_info(self, symbol: str) -> Dict:
        """Get company information."""
        endpoint = f"/v3/reference/tickers/{symbol}"
        return await self._make_request(endpoint)

    async def close(self):
        """Close the session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
