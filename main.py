import argparse
from backtesting import Backtest
from logger import logger
from core.config.settings import config
from data_processing import (
    load_data,
    add_technical_indicators,
)
from strategy_factory import StrategyFactory
from performance_metrics import (
    calculate_sortino_ratio,
    calculate_calmar_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_expectancy,
)
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from infrastructure.tasks import run_optimization
from celery import group
from core.cache import redis_cache
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.security.middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    AuditMiddleware,
)
from prometheus_fastapi_instrumentator import Instrumentator
from core.metrics import MetricsCollector
from core.security.csrf import CSRFMiddleware
from core.security.session import SessionMiddleware

# Create FastAPI app
app = FastAPI(title="BackTest AI API")

# Add middleware
app.add_middleware(CSRFMiddleware)
app.add_middleware(SessionMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuditMiddleware)

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(app)

# Create metrics collector instance
metrics = MetricsCollector()


def walk_forward_optimization(
    df, strategy_class, train_size, test_size, step_size, optimization_params, **kwargs
):
    """
    Distributed walk-forward optimization using Celery
    """
    tasks = []
    results = []

    # Create tasks for each time window
    for i in range(0, len(df) - train_size - test_size + 1, step_size):
        train_start = df.index[i]
        train_end = df.index[i + train_size - 1]
        test_start = df.index[i + train_size]
        test_end = df.index[i + train_size + test_size - 1]

        # Create task for this window
        task = run_optimization.s(
            df.to_json(),
            strategy_class.__name__,
            (train_start.isoformat(), train_end.isoformat()),
            (test_start.isoformat(), test_end.isoformat()),
            optimization_params,
            **kwargs,
        )
        tasks.append(task)

    # Execute tasks in parallel
    job = group(tasks)
    result = job.apply_async()

    try:
        # Wait for all tasks to complete with timeout
        results = result.get(timeout=3600)  # 1 hour timeout
    except Exception as e:
        logger.error(f"Walk-forward optimization failed: {str(e)}", exc_info=True)
        raise

    return results


def main():
    parser = argparse.ArgumentParser(description="Run backtesting on trading strategy.")
    parser.add_argument(
        "--data_file", type=str, required=True, help="Path to the data file"
    )
    parser.add_argument(
        "--initial_cash", type=float, default=10000, help="Initial cash for backtesting"
    )
    parser.add_argument(
        "--commission", type=float, default=0.001, help="Commission rate for trades"
    )
    parser.add_argument(
        "--slippage", type=float, default=0.001, help="Slippage rate for trades"
    )
    parser.add_argument(
        "--model_dir",
        type=str,
        default="models",
        help="Directory to save trained models",
    )
    args = parser.parse_args()
    df = load_data(args.data_file)
    df = add_technical_indicators(df)
    strategy = StrategyFactory.create_strategy(config.strategy_name)
    optimization_params = {
        "n1": range(5, 30, 5),
        "n2": range(10, 60, 5),
        "rsi_period": range(10, 30, 2),
        "rsi_overbought": range(60, 85, 5),
        "rsi_oversold": range(20, 45, 5),
    }
    # Perform walk-forward optimization
    wfo_results = walk_forward_optimization(
        df,
        strategy.__class__,
        train_size=int(len(df) * 0.6),
        test_size=int(len(df) * 0.2),
        step_size=int(len(df) * 0.1),
        optimization_params=optimization_params,
        cash=args.initial_cash,
        commission=args.commission,
        slippage=args.slippage,
        exclusive_orders=True,
    )
    # Run final backtest with optimized parameters
    best_params = max(wfo_results, key=lambda x: x["test_sharpe"])["params"]
    optimized_strategy = strategy.__class__(**best_params)
    bt = Backtest(
        df,
        optimized_strategy,
        cash=args.initial_cash,
        commission=args.commission,
        slippage=args.slippage,
        exclusive_orders=True,
    )
    stats = bt.run()
    # Calculate additional performance metrics
    returns = pd.Series(stats._equity_curve["Equity"].pct_change().dropna())
    trades = pd.Series(stats._trades["PnL"])
    # Calculate additional performance metrics
    additional_metrics = {
        "Sortino Ratio": calculate_sortino_ratio(returns),
        "Calmar Ratio": calculate_calmar_ratio(returns),
        "Max Drawdown": calculate_max_drawdown(returns),
        "Win Rate": calculate_win_rate(trades),
        "Profit Factor": calculate_profit_factor(trades),
        "Expectancy": calculate_expectancy(trades),
    }
    logger.info(f"Backtest Statistics:\n{stats}")
    logger.info(f"Additional Performance Metrics:\n{additional_metrics}")

    # Equity curve
    plt.figure(figsize=(12, 6))
    stats._equity_curve["Equity"].plot()
    plt.title("Equity Curve")
    plt.xlabel("Date")
    plt.ylabel("Equity")
    plt.savefig("equity_curve.png")
    plt.close()

    # Drawdown
    plt.figure(figsize=(12, 6))
    stats._equity_curve["DrawdownPct"].plot()
    plt.title("Drawdown")
    plt.xlabel("Date")
    plt.ylabel("Drawdown %")
    plt.savefig("drawdown.png")
    plt.close()

    # Return distribution
    plt.figure(figsize=(12, 6))
    sns.histplot(returns, kde=True)
    plt.title("Return Distribution")
    plt.xlabel("Return")
    plt.ylabel("Frequency")
    plt.savefig("return_distribution.png")
    plt.close()

    # Save trained models
    strategy.model_facade.save_all_models(args.model_dir)


if __name__ == "__main__":
    main()
