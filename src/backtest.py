# src/backtest.py

## Imports
import pandas as pd
import numpy as np


## Functions
def run_backtest(df: pd.DataFrame) -> pd.DataFrame:
	"""
	Calculate profit and loss from historical trading signals.

	run_backtest simulates how a pairs trading strategy would have performed
	in the past by applying trading signals to actual spread movements.
	It tracks daily profits and losses, accounting for the fact that we can
	only trade based on yesterday's signal (preventing look-ahead bias).

	The function calculates how much money we would have made or lost each day
	if we had followed the trading signals exactly as they were generated.

	Args:
		df : pd.DataFrame
			DataFrame containing 'spread' and 'signal' columns.
			- spread: the price difference between two assets
			- signal: +1 (long), -1 (short), 0 (flat)

	Returns:
		pd.DataFrame
			The original DataFrame with three new columns added:
				- 'spread_ret' : percentage change in spread from previous day
				- 'pnl'        : profit or loss for each day
				- 'cum_pnl'    : running total of all profits and losses

	Example:
		>>> df = pd.DataFrame({
		...     'spread': [100, 110, 105],
		...     'signal': [1, 1, 1]
		... })
		>>> result = run_backtest(df)
		>>> result['pnl'].iloc[1]  # Long position, spread increased 10%
		0.10
	"""

	# Validate input columns exist
	if not {"spread", "signal"}.issubset(df.columns):
		raise ValueError("Input DataFrame must contain 'spread' and 'signal' columns.")

	# Handle empty DataFrame gracefully
	if df.empty:
		return df

	# Make a copy so we don't modify the original data
	out = df.copy()

	# Calculate percentage change in spread from one day to the next
	# This tells us how much the price relationship moved
	out["spread_ret"] = out["spread"].pct_change().fillna(0)

	# Use yesterday's signal for today's trade to prevent look-ahead bias
	# We can only act on information available before today
	out["signal_shifted"] = out["signal"].shift(1).fillna(0)

	# Calculate profit or loss for each day
	# If we're long (+1) and spread increases, we profit
	# If we're short (-1) and spread decreases, we profit
	out["pnl"] = out["signal_shifted"] * out["spread_ret"]

	# Track cumulative profit/loss over the entire period
	out["cum_pnl"] = out["pnl"].cumsum()

	# Drop the temporary shifted signal column before returning
	out = out.drop(columns=["signal_shifted"])

	return out
