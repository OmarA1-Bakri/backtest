"""Example usage of the MarketDataAPIService."""

import asyncio
from datetime import datetime, timedelta
from data.market_data_api import MarketDataAPIService
from data.providers.factory import ProviderType


async def main():
    """Run market data examples."""
    # Initialize the service with Polygon.io as default provider
    service = MarketDataAPIService(default_provider=ProviderType.POLYGON)

    try:
        # Example 1: Get historical data for a single stock
        print("\nFetching historical data for AAPL...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        df = await service.get_historical_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            interval="1d",
        )
        print("\nAAPL Historical Data:")
        print(df.head())

        # Example 2: Get data for multiple stocks
        symbols = ["MSFT", "GOOGL", "AMZN"]
        print(f"\nFetching data for multiple stocks: {symbols}...")

        data_dict = await service.get_multiple_stocks(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval="1d",
        )

        for symbol, data in data_dict.items():
            print(f"\n{symbol} Data:")
            print(data.head())

        # Example 3: Get latest prices
        all_symbols = ["AAPL"] + symbols
        print(f"\nFetching latest prices for: {all_symbols}...")

        prices = await service.get_latest_prices(symbols=all_symbols)
        for symbol, price in prices.items():
            print(f"{symbol}: ${price:.2f}")

        # Example 4: Get company information
        print("\nFetching company information for AAPL...")
        company_info = await service.get_company_info("AAPL")
        print("\nCompany Information:")
        for key, value in company_info.items():
            print(f"{key}: {value}")

        # Example 5: Using Alpha Vantage explicitly
        print("\nFetching TSLA data from Alpha Vantage...")
        df = await service.get_historical_data(
            symbol="TSLA",
            start_date=start_date,
            end_date=end_date,
            interval="1d",
            provider=ProviderType.ALPHA_VANTAGE,
        )
        print("\nTSLA Historical Data (Alpha Vantage):")
        print(df.head())

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        # Clean up
        await service.close()


if __name__ == "__main__":
    asyncio.run(main())
