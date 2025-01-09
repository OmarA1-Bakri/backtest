from typing import Dict, Any, Tuple
import pandas as pd
from infrastructure.celery_config import celery_app
from backtesting import Backtest
from core.cache import redis_cache
from logger import logger


@celery_app.task(name="backtest.tasks.optimization.run_optimization")
def run_optimization(
    df_json: str,
    strategy_class: str,
    train_period: Tuple[str, str],
    test_period: Tuple[str, str],
    optimization_params: Dict[str, Any],
    **kwargs,
) -> Dict[str, Any]:
    """
    Distributed task for running strategy optimization on a specific time period.
    """
    try:
        # Deserialize data
        df = pd.read_json(df_json)
        train_data = df[train_period[0] : train_period[1]]
        test_data = df[test_period[0] : test_period[1]]

        # Generate cache key
        cache_key = f"opt_{strategy_class}_{train_period[0]}_{train_period[1]}"
        cached_result = redis_cache.get(cache_key)

        if cached_result:
            logger.info(f"Found cached optimization result for {cache_key}")
            return cached_result

        # Run optimization
        bt = Backtest(train_data, strategy_class, **kwargs)
        stats = bt.optimize(maximize="Sharpe Ratio", **optimization_params)

        # Run test period with optimized parameters
        optimized_strategy = strategy_class(**stats._strategy)
        bt_test = Backtest(test_data, optimized_strategy, **kwargs)
        test_stats = bt_test.run()

        result = {
            "train_period": train_period,
            "test_period": test_period,
            "train_sharpe": stats["Sharpe Ratio"],
            "test_sharpe": test_stats["Sharpe Ratio"],
            "params": stats._strategy,
            "test_metrics": {
                "max_drawdown": test_stats["Max. Drawdown"],
                "win_rate": test_stats["Win Rate"],
                "profit_factor": test_stats["Profit Factor"],
            },
        }

        # Cache result
        redis_cache.set(cache_key, result, ex=3600)  # Cache for 1 hour

        return result

    except Exception as e:
        logger.error(f"Optimization task failed: {str(e)}", exc_info=True)
        raise
