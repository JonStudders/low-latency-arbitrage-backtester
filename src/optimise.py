# src/optimize.py

## Imports
import itertools
from dataclasses import dataclass
from typing import Iterable, List, Tuple, Dict, Any, Optional

import numpy as np
import pandas as pd
from tqdm import tqdm

from preprocess import prepare_spread
from signals import generate_trade_signals
from backtest import run_backtest
from metrics import calculate_performance_metrics


## Data Classes
@dataclass
class GridSearchConfig:
	"""Configuration for parameter grid search optimisation.
	
	GridSearchConfig defines the parameter space to explore during optimisation
	and quality thresholds to filter out unreliable configurations.
	
	Attributes:
		lookbacks : Iterable[int]
			Rolling window sizes to test for spread calculation.
		entry_zs : Iterable[float]
			Z-score thresholds for entering positions.
		exit_zs : Iterable[float]
			Z-score thresholds for exiting positions.
		min_trades : int, default = 10
			Minimum number of trades required for valid configuration.
			Filters out parameter sets with insufficient trading activity.
		min_obs : int, default = 200
			Minimum observations required after warmup period.
			Ensures adequate sample size for statistical reliability.
	
	Example:
		>>> config = GridSearchConfig(
		...     lookbacks=[30, 60, 90],
		...     entry_zs=[1.5, 2.0, 2.5],
		...     exit_zs=[0.25, 0.5, 0.75],
		...     min_trades=10,
		...     min_obs=200
		... )
	"""
	lookbacks: Iterable[int]
	entry_zs: Iterable[float]
	exit_zs: Iterable[float]
	min_trades: int = 10
	min_obs: int = 200


## Functions
def _single_run(df_prices: pd.DataFrame, lookback: int, entry_z: float, exit_z: float) -> Optional[Dict[str, Any]]:
	"""Execute complete backtest pipeline for a single parameter configuration.
	
	_single_run processes the full trading strategy workflow from spread calculation
	through to performance metrics for one specific set of parameters. This function
	is designed to fail gracefully, returning None if any step encounters an error,
	which prevents a single bad configuration from terminating the entire grid search.
	
	Args:
		df_prices : pd.DataFrame
			DataFrame containing two columns of historical price data.
		lookback : int
			Rolling window size for spread statistics calculation.
		entry_z : float
			Z-score threshold for entering positions.
		exit_z : float
			Z-score threshold for exiting positions.
	
	Returns:
		Optional[Dict[str, Any]]
			Dictionary containing parameters and all performance metrics,
			or None if the configuration failed to produce valid results.
			Includes: lookback, entry_z, exit_z, observations, and all
			metrics from calculate_performance_metrics().
	
	Notes:
		- Returns None if processed data has fewer than 2 observations
		- Returns None if any exception occurs during pipeline execution
		- Fail-soft design ensures grid search continues despite individual failures
	"""
	try:
		processed = prepare_spread(df_prices, lookback=lookback)
		if processed.shape[0] < 2:
			return None

		with_signals = generate_trade_signals(processed, entry_z=entry_z, exit_z=exit_z)
		bt = run_backtest(with_signals)
		metrics = calculate_performance_metrics(bt)

		out = {
			"lookback": lookback,
			"entry_z": entry_z,
			"exit_z": exit_z,
			"observations": int(bt.shape[0]),
			**metrics
		}
		return out
	except Exception as e:
		# Fail-soft so one bad configuration doesn't kill the entire sweep
		return None


def grid_search(df_prices: pd.DataFrame, cfg: GridSearchConfig, show_progress: bool = True) -> pd.DataFrame:
	"""Perform exhaustive grid search across parameter combinations.
	
	grid_search evaluates all possible combinations of lookback windows,
	entry thresholds, and exit thresholds to identify optimal parameter
	sets for the pairs trading strategy. Each configuration is backtested
	and ranked by risk-adjusted performance metrics.
	
	The function applies quality filters to exclude unreliable configurations
	with insufficient trading activity or inadequate sample sizes. Results
	are sorted by Sharpe ratio (primary), total return (secondary), and
	maximum drawdown (tertiary) to prioritise risk-adjusted performance.
	
	Args:
		df_prices : pd.DataFrame
			DataFrame containing two columns of historical price data.
			Must have exactly two columns representing the asset pair.
		cfg : GridSearchConfig
			Configuration object defining parameter ranges and quality filters.
		show_progress : bool, default = True
			Whether to display progress bar during grid search.
	
	Returns:
		pd.DataFrame
			DataFrame with one row per valid configuration, sorted by performance.
			Columns include:
				- lookback, entry_z, exit_z (parameters)
				- observations (post-warmup sample size)
				- all metrics from calculate_performance_metrics()
				- return_per_trade (derived metric)
				- drawdown_to_return (derived risk metric)
			Returns empty DataFrame if no configurations pass quality filters.
	
	Example:
		>>> config = GridSearchConfig(
		...     lookbacks=[30, 60, 90],
		...     entry_zs=[1.5, 2.0, 2.5],
		...     exit_zs=[0.25, 0.5, 0.75]
		... )
		>>> results = grid_search(df_prices, config)
		>>> best = results.iloc[0]  # Top-ranked configuration
		>>> print(f"Best Sharpe: {best['sharpe_ratio']:.2f}")
	
	Notes:
		- Configurations where entry_z <= exit_z are automatically skipped
		- Invalid configurations (errors, insufficient data) are silently filtered
		- Progress bar can be disabled for batch processing
		- Sorting prioritises Sharpe ratio over absolute returns
	"""
	# Validate input DataFrame has exactly two columns
	if df_prices.shape[1] != 2:
		raise ValueError("Input DataFrame must contain exactly two columns for pair trading.")
	
	# Handle empty DataFrame gracefully
	if df_prices.empty:
		print("Warning: Empty DataFrame provided to grid_search.")
		return pd.DataFrame()
	
	records: List[Dict[str, Any]] = []
	
	# Generate all parameter combinations
	param_combinations = list(itertools.product(cfg.lookbacks, cfg.entry_zs, cfg.exit_zs))
	total_combinations = len(param_combinations)
	
	print(f"Testing {total_combinations} parameter combinations...")
	
	# Iterate through all combinations with optional progress bar
	iterator = tqdm(param_combinations, desc="Grid search") if show_progress else param_combinations
	
	for lb, ez, xz in iterator:
		if ez <= xz:
			# Invalid by design - would cause signal chattering
			continue
		
		result = _single_run(df_prices, lb, ez, xz)
		if result is None:
			continue
		
		# Apply quality filters to ensure statistical reliability
		if result["observations"] < cfg.min_obs:
			continue
		if result["num_trades"] < cfg.min_trades:
			continue
		
		records.append(result)
	
	# Handle case where no configurations passed filters
	if not records:
		print("Warning: No configurations passed quality filters.")
		return pd.DataFrame(columns=[
			"lookback", "entry_z", "exit_z", "observations",
			"total_return", "sharpe_ratio", "sortino_ratio", "max_drawdown",
			"win_rate", "num_trades", "turnover", "avg_win", "avg_loss", "profit_factor"
		])
	
	df = pd.DataFrame.from_records(records)
	
	print(f"Found {len(df)} valid configurations.")
	
	# Calculate derived metrics for additional insight
	df["return_per_trade"] = np.where(df["num_trades"] > 0, df["total_return"] / df["num_trades"], np.nan)
	df["drawdown_to_return"] = np.where(df["total_return"] != 0, df["max_drawdown"] / abs(df["total_return"]), np.nan)
	
	# Sort by composite score: Sharpe ratio (primary), total return (secondary), max drawdown (tertiary)
	df = df.sort_values(
		by=["sharpe_ratio", "total_return", "max_drawdown"],
		ascending=[False, False, True]
	).reset_index(drop=True)
	
	return df


def best_config(df_prices: pd.DataFrame, cfg: GridSearchConfig, show_progress: bool = True) -> Dict[str, Any]:
	"""Identify optimal parameter configuration from grid search results.
	
	best_config is a convenience function that runs a complete grid search
	and returns the top-ranked parameter set based on risk-adjusted performance.
	The ranking prioritises Sharpe ratio, followed by total return and drawdown.
	
	Args:
		df_prices : pd.DataFrame
			DataFrame containing two columns of historical price data.
		cfg : GridSearchConfig
			Configuration object defining parameter ranges and quality filters.
		show_progress : bool, default = True
			Whether to display progress bar during grid search.
	
	Returns:
		Dict[str, Any]
			Dictionary containing the best parameter set and its metrics.
			Returns empty dict if no valid configurations found.
			Includes all columns from grid_search() for the top-ranked row.
	
	Example:
		>>> config = GridSearchConfig(
		...     lookbacks=[30, 60, 90],
		...     entry_zs=[1.5, 2.0, 2.5],
		...     exit_zs=[0.25, 0.5, 0.75]
		... )
		>>> best = best_config(df_prices, config)
		>>> print(f"Optimal lookback: {best['lookback']}")
		>>> print(f"Optimal entry_z: {best['entry_z']}")
		>>> print(f"Sharpe ratio: {best['sharpe_ratio']:.2f}")
	
	Notes:
		- Returns empty dict if grid search produces no valid results
		- Top configuration is selected by Sharpe ratio (primary criterion)
		- Consider examining full grid_search() results for robustness analysis
	"""
	res = grid_search(df_prices, cfg, show_progress=show_progress)
	return {} if res.empty else res.iloc[0].to_dict()
