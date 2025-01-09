from strategy import ImprovedTMCS
from strategy import SimpleMAStrategy
from strategy import Strategy


class StrategyFactory:
    @staticmethod
    def create_strategy(strategy_name: str) -> Strategy:
        strategies = {
            "improved_tmcs": ImprovedTMCS,
            "simple_ma": SimpleMAStrategy,
        }
        return strategies.get(strategy_name.lower())()
