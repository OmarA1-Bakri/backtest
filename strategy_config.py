from dataclasses import dataclass


@dataclass
class ImprovedTMCSConfig:
    entry_threshold: float = 0.5
    exit_threshold: float = 0.5


@dataclass
class StrategyConfig:
    ImprovedTMCS: ImprovedTMCSConfig = ImprovedTMCSConfig()
    # Add configurations for other strategies here


strategy_config = StrategyConfig()
