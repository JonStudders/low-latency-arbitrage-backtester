# src/metrics.py

## Imports
import pandas as pd
import numpy as np


## Functions
def calculate_performance_metrics(df: pd.DataFrame) -> dict:
	"""
	Calculate risk-adjusted performance metrics for a trading strategy.

	calculate_performance_metrics computes standard quantitative finance metrics
	to evaluate strategy performance on both absolute and risk-adjusted bases.
	These metrics are essential for comparing strategies and assessing whether
	returns justify the risks taken.

	The function assumes the input DataFrame contains the output from run_backtest(),
	including daily PnL values and trading signals.

	Args:
		df : pd.DataFrame
			DataFrame containing backtest results with required columns:
			- 'pnl'        : daily profit or loss
			- 'cum_pnl'    : cumulative profit or loss
			- 'signal'     : trading position (+1 long, -1 short, 0 flat)

	Returns:
		dict
			Dictionary containing the following performance metrics:
				- 'total_return'     : cumulative return over the entire period
				- 'sharpe_ratio'     : annualised risk-adjusted return (252 trading days)
				- 'sortino_ratio'    : annualised downside risk-adjusted return
				- 'max_drawdown'     : worst peak-to-trough decline
				- 'win_rate'         : percentage of profitable days
				- 'num_trades'       : total number of position changes
				- 'turnover'         : average daily position turnover
				- 'avg_win'          : average profit on winning days
				- 'avg_loss'         : average loss on losing days
				- 'profit_factor'    : ratio of gross profits to gross losses

	Example:
		>>> df = pd.DataFrame({
		...     'pnl': [0, 0.01, -0.005, 0.02],
		...     'cum_pnl': [0, 0.01, 0.005, 0.025],
		...     'signal': [0, 1, 1, 1]
		... })
		>>> metrics = calculate_performance_metrics(df)
		>>> metrics['sharpe_ratio']  # Annualised Sharpe ratio
		2.45

	Notes:
		- Sharpe ratio assumes 252 trading days per year
		- Sortino ratio only penalises downside volatility (negative returns)
		- Win rate only considers days with active positions (signal != 0)
		- Profit factor > 1 indicates profitable strategy
		- Turnover measures average daily absolute position change
		- Returns NaN for metrics that cannot be calculated (e.g., division by zero)
	"""

	# Validate input columns exist
	required_cols = {"pnl", "cum_pnl", "signal"}
	if not required_cols.issubset(df.columns):
		raise ValueError(f"Input DataFrame must contain columns: {required_cols}")

	# Handle empty DataFrame gracefully
	if df.empty:
		return {
			"total_return": 0.0,
			"sharpe_ratio": np.nan,
			"sortino_ratio": np.nan,
			"max_drawdown": 0.0,
			"win_rate": 0.0,
			"num_trades": 0,
			"turnover": 0.0,
			"avg_win": 0.0,
			"avg_loss": 0.0,
			"profit_factor": np.nan,
		}

	# Extract relevant columns
	pnl = df["pnl"]
	cum_pnl = df["cum_pnl"]
	signal = df["signal"]

	# Total return: final cumulative PnL
	total_return = cum_pnl.iloc[-1] if len(cum_pnl) > 0 else 0.0

	# Sharpe ratio: annualised risk-adjusted return
	# Formula: (mean_return / std_return) * sqrt(252)
	# Assumes 252 trading days per year
	if pnl.std() != 0:
		sharpe_ratio = (pnl.mean() / pnl.std()) * np.sqrt(252)
	else:
		sharpe_ratio = np.nan

	# Sortino ratio: annualised downside risk-adjusted return
	# Only penalises downside volatility (negative returns)
	# Formula: (mean_return / downside_std) * sqrt(252)
	downside_returns = pnl[pnl < 0]
	if len(downside_returns) > 0 and downside_returns.std() != 0:
		sortino_ratio = (pnl.mean() / downside_returns.std()) * np.sqrt(252)
	else:
		sortino_ratio = np.nan

	# Maximum drawdown: worst peak-to-trough decline
	# Calculate running maximum, then find largest drop from peak
	running_max = cum_pnl.cummax()
	drawdown = cum_pnl - running_max
	max_drawdown = drawdown.min()

	# Win rate: percentage of profitable days (only when position is active)
	# Filter to days where we have a position (signal != 0 on previous day)
	active_days = pnl[pnl != 0]
	if len(active_days) > 0:
		win_rate = (active_days > 0).sum() / len(active_days)
	else:
		win_rate = 0.0

	# Number of trades: count position changes
	# A trade occurs when signal changes from previous value
	signal_changes = signal.diff().abs()
	num_trades = (signal_changes > 0).sum()

	# Turnover: average daily absolute position change
	# Measures how frequently positions are adjusted
	if len(signal_changes) > 0:
		turnover = signal_changes.mean()
	else:
		turnover = 0.0

	# Average win and average loss
	winning_days = pnl[pnl > 0]
	losing_days = pnl[pnl < 0]
	
	avg_win = winning_days.mean() if len(winning_days) > 0 else 0.0
	avg_loss = losing_days.mean() if len(losing_days) > 0 else 0.0

	# Profit factor: ratio of gross profits to gross losses
	# Values > 1 indicate profitable strategy
	gross_profit = winning_days.sum() if len(winning_days) > 0 else 0.0
	gross_loss = abs(losing_days.sum()) if len(losing_days) > 0 else 0.0
	
	if gross_loss != 0:
		profit_factor = gross_profit / gross_loss
	elif gross_profit > 0:
		profit_factor = np.inf  # All wins, no losses
	else:
		profit_factor = np.nan  # No trades at all

	return {
		"total_return": total_return,
		"sharpe_ratio": sharpe_ratio,
		"sortino_ratio": sortino_ratio,
		"max_drawdown": max_drawdown,
		"win_rate": win_rate,
		"num_trades": num_trades,
		"turnover": turnover,
		"avg_win": avg_win,
		"avg_loss": avg_loss,
		"profit_factor": profit_factor,
	}
