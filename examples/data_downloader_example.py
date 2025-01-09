"""Example usage of the MarketDataDownloader."""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from data.downloader import MarketDataDownloader
from data.exporter import ExportFormat


async def main():
    """Run data downloader examples."""
    # Initialize downloader with cache directory
    cache_dir = Path("data/cache")
    downloader = MarketDataDownloader(
        cache_dir=cache_dir,
        export_format=ExportFormat.PARQUET,
        update_interval=timedelta(hours=12),
    )

    try:
        # Example 1: Get historical data for a single stock
        print("\nFetching historical data for AAPL...")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        # First fetch will download from API
        print("First fetch (from API)...")
        df = await downloader.get_historical_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            interval="1d",
        )
        print("\nAAPL Historical Data:")
        print(df.head())

        # Second fetch should use cache
        print("\nSecond fetch (from cache)...")
        df_cached = await downloader.get_historical_data(
            symbol="AAPL",
            start_date=start_date,
            end_date=end_date,
            interval="1d",
        )
        print("Data retrieved from cache")

        # Example 2: Get data for multiple stocks
        symbols = ["MSFT", "GOOGL", "AMZN"]
        print(f"\nFetching data for multiple stocks: {symbols}...")

        data_dict = await downloader.get_multiple_stocks(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            interval="1d",
        )

        for symbol, data in data_dict.items():
            print(f"\n{symbol} Data:")
            print(data.head())

        # Example 3: Force update cache for specific symbols
        print("\nUpdating cache for all symbols...")
        all_symbols = ["AAPL"] + symbols
        await downloader.update_cache(
            symbols=all_symbols,
            days_of_history=90,  # Cache 90 days of history
            intervals=["1d", "5m"],  # Cache both daily and 5-minute data
        )
        print("Cache update complete")

    except Exception as e:
        print(f"Error: {str(e)}")

    finally:
        # Clean up
        await downloader.close()


if __name__ == "__main__":
    asyncio.run(main())
