from base.base_strategy import BaseStrategy
from simple_ma_strategy import SimpleMAStrategy
from advanced_strategy import AdaptiveMLStrategy


class StrategyFactory:
    """Factory for creating trading strategy instances."""

    @staticmethod
    def create_strategy(strategy_name: str) -> BaseStrategy:
        """Create a strategy instance based on the given name.

        Args:
            strategy_name: Name of the strategy to create

        Returns:
            Strategy instance
        """
        if strategy_name == "ImprovedTMCS":
            from strategy import ImprovedTMCS

            return ImprovedTMCS
        elif strategy_name == "SimpleMAStrategy":
            return SimpleMAStrategy
        elif strategy_name == "AdaptiveMLStrategy":
            return AdaptiveMLStrategy
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
