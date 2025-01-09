import numpy as np
from typing import Dict, Any
from logger import logger


class RiskAnalyzer:
    """Analyzes portfolio risk and performance metrics."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize risk analyzer."""
        self.config = config
        logger.info("Risk analyzer initialized.")

    def calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate the maximum drawdown from returns.

        Args:
            returns: Historical returns array

        Returns:
            Maximum drawdown
        """
        try:
            cum_returns = (1 + returns).cumprod()
            rolling_max = np.maximum.accumulate(cum_returns)
            drawdowns = (cum_returns - rolling_max) / rolling_max
            max_drawdown = abs(min(drawdowns))
            logger.info(f"Calculated max drawdown: {max_drawdown:.2f}")
            return max_drawdown
        except Exception as e:
            logger.error(f"Error calculating max drawdown: {e}")
            return 0.0

    def calculate_var(
        self, returns: np.ndarray, confidence_level: float = 0.95
    ) -> float:
        """Calculate Value at Risk (VaR) for the given confidence level.

        Args:
            returns: Historical returns array
            confidence_level: Confidence level for VaR calculation

        Returns:
            Value at Risk
        """
        try:
            var = np.percentile(returns, (1 - confidence_level) * 100)
            logger.info(
                f"Calculated VaR at {confidence_level*100}% confidence level: {var}"
            )
            return var
        except Exception as e:
            logger.error(f"Error calculating VaR: {e}")
            return 0.0

    def calculate_expected_shortfall(
        self, returns: np.ndarray, confidence_level: float = 0.95
    ) -> float:
        """Calculate Expected Shortfall (ES) for the given confidence level.

        Args:
            returns: Historical returns array
            confidence_level: Confidence level for ES calculation

        Returns:
            Expected Shortfall
        """
        try:
            var = self.calculate_var(returns, confidence_level)
            es = returns[returns <= var].mean()
            logger.info(
                f"Calculated Expected Shortfall at {confidence_level*100}% confidence level: {es}"
            )
            return es
        except Exception as e:
            logger.error(f"Error calculating Expected Shortfall: {e}")
            return 0.0
