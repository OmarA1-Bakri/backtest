"""Base classes for data providers."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Union
import pandas as pd


class DataProvider(ABC):
    """Abstract base class for data providers."""

    @abstractmethod
    async def get_stock_data(
        self,
        symbol: str,
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get stock data for a given symbol and date range."""
        pass

    @abstractmethod
    async def get_multiple_stocks(
        self,
        symbols: List[str],
        start_date: Union[str, datetime],
        end_date: Union[str, datetime],
        interval: str = "1d",
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple stocks."""
        pass

    @abstractmethod
    async def get_latest_price(self, symbol: str) -> float:
        """Get the latest price for a symbol."""
        pass

    @abstractmethod
    async def get_company_info(self, symbol: str) -> Dict:
        """Get company information."""
        pass
