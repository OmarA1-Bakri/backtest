from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, REGISTRY
from prometheus_client.exposition import generate_latest
from prometheus_client.core import GaugeMetricFamily
import psutil
from typing import Dict, Any, Optional, Tuple
import time

# Create a custom registry to handle historical timestamps
registry = CollectorRegistry()


class TimestampedGauge(GaugeMetricFamily):
    def __init__(self, name: str, documentation: str, labels: Optional[list] = None):
        """Initialize TimestampedGauge.

        Args:
            name: Metric name
            documentation: Metric documentation
            labels: Optional list of label names
        """
        super().__init__(name, documentation, labels=labels)
        self._values = {}
        self._name = name
        self._documentation = documentation
        self._labels = labels or []

    def set_with_timestamp(
        self, value: float, timestamp: float, labels: Optional[list] = None
    ) -> None:
        """Set metric value with timestamp.

        Args:
            value: Metric value
            timestamp: Unix timestamp
            labels: Optional list of label values
        """
        if labels:
            label_tuple = tuple(str(l) for l in labels)
        else:
            label_tuple = ()
        self._values[label_tuple] = (value, timestamp)

    def collect(self) -> list:
        """Collect all metric values.

        Returns:
            list: List of metrics
        """
        for labels, (value, timestamp) in self._values.items():
            self.add_metric(
                labels, value, timestamp_ms=timestamp * 1000
            )  # Convert to milliseconds
        return [self]

    def __hash__(self) -> int:
        """Make TimestampedGauge hashable.

        Returns:
            int: Hash value
        """
        return hash((self._name, tuple(self._labels or [])))

    def __eq__(self, other: object) -> bool:
        """Compare TimestampedGauge instances.

        Args:
            other: Other TimestampedGauge instance

        Returns:
            bool: True if equal, False otherwise
        """
        if not isinstance(other, TimestampedGauge):
            return NotImplemented
        return self._name == other._name and self._labels == other._labels


class MetricsCollector:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MetricsCollector, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            # System metrics
            self.cpu_usage = Gauge(
                "system_cpu_usage", "Current CPU usage percentage", registry=registry
            )

            self.memory_usage = Gauge(
                "system_memory_usage",
                "Current memory usage in bytes",
                registry=registry,
            )

            # Task metrics
            self.task_count = Counter(
                "task_count",
                "Number of tasks processed",
                ["task_name", "status"],
                registry=registry,
            )

            self.task_latency = Histogram(
                "task_latency", "Task execution time", ["task_name"], registry=registry
            )

            self.task_queue_size = Gauge(
                "task_queue_size",
                "Current task queue size",
                ["queue_name"],
                registry=registry,
            )

            # Cache metrics
            self.cache_hits = Counter(
                "cache_hits", "Number of cache hits", ["cache_name"], registry=registry
            )

            self.cache_misses = Counter(
                "cache_misses",
                "Number of cache misses",
                ["cache_name"],
                registry=registry,
            )

            # Portfolio metrics
            self.portfolio_value = Gauge(
                "portfolio_value", "Current portfolio value", registry=registry
            )

            self.returns = Gauge("returns", "Portfolio returns", registry=registry)

            self.trade_count = Counter(
                "trade_count", "Number of trades", ["side"], registry=registry
            )

            self.trade_pnl = Counter(
                "trade_pnl", "Trade profit and loss", ["symbol"], registry=registry
            )

            self.position_value = Gauge(
                "position_value",
                "Current position value",
                ["symbol"],
                registry=registry,
            )

            # Trading Metrics with timestamps
            self.portfolio_value_trading = TimestampedGauge(
                "backtest_portfolio_value",
                "Current portfolio value",
                labels=["strategy"],
            )
            registry.register(self.portfolio_value_trading)

            self.returns_trading = TimestampedGauge(
                "backtest_returns", "Strategy returns", labels=["strategy", "timeframe"]
            )
            registry.register(self.returns_trading)

            self.drawdown = TimestampedGauge(
                "backtest_drawdown", "Strategy drawdown", labels=["strategy"]
            )
            registry.register(self.drawdown)

            # Performance Metrics
            self.execution_time = Histogram(
                "backtest_execution_time",
                "Time taken for strategy execution",
                ["strategy", "operation"],
                buckets=(
                    0.001,
                    0.005,
                    0.01,
                    0.025,
                    0.05,
                    0.075,
                    0.1,
                    0.25,
                    0.5,
                    0.75,
                    1.0,
                ),
                registry=registry,
            )

            self.memory_usage_performance = Gauge(
                "backtest_memory_usage",
                "Memory usage of the backtesting process",
                ["strategy"],
                registry=registry,
            )

            # Risk Metrics
            self.sharpe_ratio = Gauge(
                "backtest_sharpe_ratio",
                "Strategy Sharpe ratio",
                ["strategy"],
                registry=registry,
            )

            self.volatility = Gauge(
                "backtest_volatility",
                "Strategy volatility",
                ["strategy"],
                registry=registry,
            )

            self.value_at_risk = Gauge(
                "backtest_value_at_risk",
                "Strategy Value at Risk (VaR)",
                ["strategy", "confidence_level"],
                registry=registry,
            )

            self._counters = {}
            MetricsCollector._initialized = True

    def track_task(self, task_name: str, status: str):
        """Track Celery task execution."""
        self.task_count.labels(task_name=task_name, status=status).inc()

    def track_task_duration(self, task_name: str, duration: float):
        """Track task execution duration."""
        self.task_latency.labels(task_name=task_name).observe(duration)

    def update_queue_size(self, queue_name: str, size: int):
        """Update queue size metric."""
        self.task_queue_size.labels(queue_name=queue_name).set(size)

    def track_cache_operation(self, cache_name: str, hit: bool):
        """Track cache hit/miss."""
        if hit:
            self.cache_hits.labels(cache_name=cache_name).inc()
        else:
            self.cache_misses.labels(cache_name=cache_name).inc()

    def track_portfolio_value(self, value: float):
        """Track current portfolio value."""
        self.portfolio_value.set(value)

    def track_returns(self, returns: float):
        """Track portfolio returns."""
        self.returns.set(returns)

    def track_trade(self, side: str):
        """Track a trade execution."""
        self.trade_count.labels(side=side).inc()

    def track_trade_pnl(self, symbol: str, pnl: float):
        """Track trade P&L."""
        self.trade_pnl.labels(symbol=symbol).inc(pnl)

    def track_position_value(self, symbol: str, value: float):
        """Track position value."""
        self.position_value.labels(symbol=symbol).set(value)

    def update_trading_metrics(
        self, strategy_name: str, metrics: Dict[str, Any]
    ) -> None:
        """Update trading metrics with historical timestamps.

        Args:
            strategy_name: Name of the strategy
            metrics: Dictionary containing metric values and timestamp
        """
        timestamp = metrics.get("timestamp", int(time.time()))

        if "portfolio_value" in metrics:
            self.portfolio_value_trading.set_with_timestamp(
                metrics["portfolio_value"], timestamp, labels=[strategy_name]
            )

        if "returns" in metrics:
            self.returns_trading.set_with_timestamp(
                metrics["returns"], timestamp, labels=[strategy_name, "daily"]
            )

        if "drawdown" in metrics:
            self.drawdown.set_with_timestamp(
                metrics["drawdown"], timestamp, labels=[strategy_name]
            )

    def update_performance_metrics(
        self, strategy_name: str, metrics: Dict[str, Any]
    ) -> None:
        """Update performance metrics.

        Args:
            strategy_name: Name of the strategy
            metrics: Dictionary containing metric values
        """
        if "execution_time" in metrics:
            self.execution_time.labels(
                strategy=strategy_name, operation=metrics["operation"]
            ).observe(metrics["execution_time"])

        if "memory_usage" in metrics:
            self.memory_usage_performance.labels(strategy=strategy_name).set(
                metrics["memory_usage"]
            )

    def update_risk_metrics(self, strategy_name: str, metrics: Dict[str, Any]) -> None:
        """Update risk metrics.

        Args:
            strategy_name: Name of the strategy
            metrics: Dictionary containing metric values
        """
        if "sharpe_ratio" in metrics:
            self.sharpe_ratio.labels(strategy=strategy_name).set(
                metrics["sharpe_ratio"]
            )

        if "volatility" in metrics:
            self.volatility.labels(strategy=strategy_name).set(metrics["volatility"])

        if "var" in metrics:
            self.value_at_risk.labels(
                strategy=strategy_name, confidence_level="95"
            ).set(metrics["var_95"])
            self.value_at_risk.labels(
                strategy=strategy_name, confidence_level="99"
            ).set(metrics["var_99"])

    def get_metrics(self) -> bytes:
        """Generate metrics in Prometheus format with timestamps."""
        self.collect_system_metrics()
        return generate_latest(registry)

    def collect_system_metrics(self):
        """Collect system metrics."""
        self.cpu_usage.set(psutil.cpu_percent())
        memory = psutil.virtual_memory()
        self.memory_usage.set(memory.used)

    def get_counter(self, name: str) -> int:
        """Get current value of a counter metric.

        Args:
            name: Metric name

        Returns:
            Current counter value
        """
        return self._counters.get(name, 0)


# Create metrics endpoint handler
def metrics_endpoint() -> Dict[str, Any]:
    """Handler for /metrics endpoint."""
    return {
        "Content-Type": "text/plain; version=0.0.4",
        "body": MetricsCollector().get_metrics(),
    }
