import yfinance as yf
from backtesting import Backtest
from strategy import SimpleMAStrategy
import pandas as pd
from prometheus_client import start_http_server
import logging
from logger import logger
from datetime import datetime, timedelta
from data_processing import add_technical_indicators


def run_backtest():
    """Run the backtest with the SimpleMAStrategy."""
    try:
        # Start Prometheus metrics server
        start_http_server(9091)
        logger.info("Started Prometheus metrics server on port 9091")

        # Get historical data for the last year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        data = yf.download("AAPL", start=start_date, end=end_date)

        # Log data information
        logger.info(f"Original columns: {data.columns.tolist()}")

        # Prepare data for backtesting
        data.columns = [
            col[0] if isinstance(col, tuple) else col for col in data.columns
        ]
        logger.info(f"Modified columns: {data.columns.tolist()}")

        # Add technical indicators
        data = add_technical_indicators(data)
        logger.info(f"Final columns: {data.columns.tolist()}")

        # Strategy parameters
        params = {"fast_ma": 20, "slow_ma": 50}

        # Create and run backtest
        bt = Backtest(
            data, SimpleMAStrategy, cash=10000, commission=0.002, exclusive_orders=True
        )

        logger.info("Starting backtest...")
        stats = bt.run(fast_ma=params["fast_ma"], slow_ma=params["slow_ma"])
        logger.info("Backtest completed successfully")
        logger.info(f"Final portfolio value: ${stats['Equity Final [$]']:.2f}")
        logger.info(f"Total return: {stats['Return [%]']:.2f}%")
        logger.info(f"Sharpe ratio: {stats['Sharpe Ratio']:.2f}")

        return stats

    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        raise


if __name__ == "__main__":
    run_backtest()
