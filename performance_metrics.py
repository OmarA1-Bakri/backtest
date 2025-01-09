import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """Calculate the Sortino ratio for a series of returns.

    Args:
        returns: Series of returns
        risk_free_rate: Risk-free rate (default: 0.0)

    Returns:
        Sortino ratio
    """
    try:
        # Calculate excess returns
        excess_returns = returns - risk_free_rate

        # Calculate downside deviation (only negative returns)
        negative_returns = returns[returns < 0]
        downside_std = np.sqrt(np.mean(negative_returns**2))

        # Calculate Sortino ratio
        if downside_std == 0:
            return 0.0

        sortino_ratio = (excess_returns.mean() / downside_std) * np.sqrt(252)
        return sortino_ratio
    except Exception as e:
        logger.error(f"Error calculating Sortino ratio: {str(e)}")
        return 0.0


def calculate_calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Calculate the Calmar ratio for a series of returns.

    Args:
        returns: Series of returns
        periods_per_year: Number of periods in a year

    Returns:
        Calmar ratio
    """
    try:
        # Calculate annualized return
        total_return = (1 + returns).prod() - 1
        years = len(returns) / periods_per_year
        annualized_return = (1 + total_return) ** (1 / years) - 1

        # Calculate maximum drawdown
        cum_returns = (1 + returns).cumprod()
        rolling_max = cum_returns.expanding().max()
        drawdowns = cum_returns / rolling_max - 1
        max_drawdown = drawdowns.min()

        # Calculate Calmar ratio
        if max_drawdown == 0:
            return 0.0

        calmar_ratio = annualized_return / abs(max_drawdown)
        return calmar_ratio
    except Exception as e:
        logger.error(f"Error calculating Calmar ratio: {str(e)}")
        return 0.0


def calculate_max_drawdown(returns: pd.Series) -> float:
    """Calculate the maximum drawdown from a series of returns.

    Args:
        returns: Series of returns

    Returns:
        Maximum drawdown
    """
    try:
        # Calculate cumulative returns
        cum_returns = (1 + returns).cumprod()

        # Calculate running maximum
        running_max = cum_returns.expanding().max()

        # Calculate drawdowns
        drawdowns = cum_returns / running_max - 1

        # Get maximum drawdown
        max_drawdown = drawdowns.min()

        return max_drawdown
    except Exception as e:
        logger.error(f"Error calculating maximum drawdown: {str(e)}")
        return 0.0


def calculate_win_rate(returns: pd.Series) -> float:
    """Calculate the win rate from a series of returns.

    Args:
        returns: Series of returns

    Returns:
        Win rate (percentage of positive returns)
    """
    try:
        if len(returns) == 0:
            return 0.0

        wins = (returns > 0).sum()
        total_trades = len(returns)

        win_rate = wins / total_trades if total_trades > 0 else 0.0
        return win_rate
    except Exception as e:
        logger.error(f"Error calculating win rate: {str(e)}")
        return 0.0


def calculate_profit_factor(returns: pd.Series) -> float:
    """Calculate the profit factor from a series of returns.

    Args:
        returns: Series of returns

    Returns:
        Profit factor (ratio of gross profits to gross losses)
    """
    try:
        if len(returns) == 0:
            return 0.0

        profits = returns[returns > 0].sum()
        losses = abs(returns[returns < 0].sum())

        profit_factor = profits / losses if losses != 0 else float("inf")
        return profit_factor
    except Exception as e:
        logger.error(f"Error calculating profit factor: {str(e)}")
        return 0.0


def calculate_expectancy(returns: pd.Series) -> float:
    """Calculate the expectancy (average trade profit/loss) from a series of returns.

    Args:
        returns: Series of returns

    Returns:
        Expectancy (average profit/loss per trade)
    """
    try:
        if len(returns) == 0:
            return 0.0

        win_rate = calculate_win_rate(returns)
        avg_win = returns[returns > 0].mean() if len(returns[returns > 0]) > 0 else 0
        avg_loss = returns[returns < 0].mean() if len(returns[returns < 0]) > 0 else 0

        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        return expectancy
    except Exception as e:
        logger.error(f"Error calculating expectancy: {str(e)}")
        return 0.0


class PerformanceMetrics:
    @staticmethod
    def calculate_sortino_ratio(
        returns: pd.Series, risk_free_rate: float = 0.0
    ) -> float:
        """Calculate the Sortino ratio for a series of returns.

        Args:
            returns: Series of returns
            risk_free_rate: Risk-free rate (default: 0.0)

        Returns:
            Sortino ratio
        """
        try:
            # Calculate excess returns
            excess_returns = returns - risk_free_rate

            # Calculate downside deviation (only negative returns)
            negative_returns = returns[returns < 0]
            downside_std = np.sqrt(np.mean(negative_returns**2))

            # Calculate Sortino ratio
            if downside_std == 0:
                return 0.0

            sortino_ratio = (excess_returns.mean() / downside_std) * np.sqrt(252)
            return sortino_ratio
        except Exception as e:
            logger.error(f"Error calculating Sortino ratio: {str(e)}")
            return 0.0

    @staticmethod
    def calculate_calmar_ratio(returns, periods_per_year=252):
        total_return = (returns + 1).prod() - 1
        years = len(returns) / periods_per_year
        cagr = (1 + total_return) ** (1 / years) - 1
        max_drawdown = PerformanceMetrics.calculate_max_drawdown(returns)
        return cagr / abs(max_drawdown)

    @staticmethod
    def calculate_max_drawdown(returns):
        cum_returns = (1 + returns).cumprod()
        running_max = np.maximum.accumulate(cum_returns)
        drawdown = (cum_returns - running_max) / running_max
        return drawdown.min()

    @staticmethod
    def calculate_win_rate(trades):
        winning_trades = trades[trades > 0]
        return len(winning_trades) / len(trades)

    @staticmethod
    def calculate_profit_factor(trades):
        gross_profit = trades[trades > 0].sum()
        gross_loss = abs(trades[trades < 0].sum())
        return gross_profit / gross_loss if gross_loss != 0 else np.inf

    @staticmethod
    def calculate_expectancy(trades):
        avg_win = trades[trades > 0].mean() if len(trades[trades > 0]) > 0 else 0
        avg_loss = abs(trades[trades < 0].mean()) if len(trades[trades < 0]) > 0 else 0
        win_rate = PerformanceMetrics.calculate_win_rate(trades)
        return (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
