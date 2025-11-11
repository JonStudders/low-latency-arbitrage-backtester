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
		>>> print(f"Best Sharpe: {round(best['sharpe_ratio'], 2)}")
	
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
		>>> print(f"Sharpe ratio: {round(best['sharpe_ratio'], 2)}")
	
	Notes:
		- Returns empty dict if grid search produces no valid results
		- Top configuration is selected by Sharpe ratio (primary criterion)
		- Consider examining full grid_search() results for robustness analysis
	"""
	res = grid_search(df_prices, cfg, show_progress=show_progress)
	return {} if res.empty else res.iloc[0].to_dict()


def walk_forward_validation(df_prices: pd.DataFrame, cfg: GridSearchConfig, 
                            train_fraction: float = 0.7, show_progress: bool = True) -> Dict[str, Any]:
	"""Perform walk-forward validation with train/test split.
	
	walk_forward_validation splits the data into training and testing periods,
	optimises parameters on the training set, then validates performance on
	the unseen test set. This helps detect overfitting and assess whether
	optimal parameters generalise to new data.
	
	Args:
		df_prices : pd.DataFrame
			DataFrame containing two columns of historical price data.
		cfg : GridSearchConfig
			Configuration object defining parameter ranges and quality filters.
		train_fraction : float, default = 0.7
			Fraction of data to use for training (0.0 to 1.0).
			Remaining fraction is used for testing.
		show_progress : bool, default = True
			Whether to display progress bar during optimisation.
	
	Returns:
		Dict[str, Any]
			Dictionary containing:
				- train_best: Best configuration from training period
				- test_metrics: Performance metrics on test period using train_best params
				- train_sharpe: Sharpe ratio on training data
				- test_sharpe: Sharpe ratio on test data
				- sharpe_degradation: Percentage drop in Sharpe from train to test
	
	Example:
		>>> config = GridSearchConfig(
		...     lookbacks=[30, 60, 90],
		...     entry_zs=[1.5, 2.0, 2.5],
		...     exit_zs=[0.25, 0.5, 0.75]
		... )
		>>> result = walk_forward_validation(df_prices, config, train_fraction=0.7)
		>>> print(f"Train Sharpe: {round(result['train_sharpe'], 2)}")
		>>> print(f"Test Sharpe: {round(result['test_sharpe'], 2)}")
		>>> print(f"Degradation: {round(result['sharpe_degradation'], 1)}%")
	
	Notes:
		- Large degradation suggests overfitting to training period
		- Negative test Sharpe indicates parameters don't generalise
		- Consider multiple walk-forward windows for robustness
	"""
	if not 0.0 < train_fraction < 1.0:
		raise ValueError("train_fraction must be between 0.0 and 1.0")
	
	# Split data into train and test
	split_idx = int(len(df_prices) * train_fraction)
	df_train = df_prices.iloc[:split_idx].copy()
	df_test = df_prices.iloc[split_idx:].copy()
	
	print(f"Train period: {len(df_train)} rows")
	print(f"Test period:  {len(df_test)} rows\n")
	
	# Optimise on training data
	print("Optimising on training data...")
	train_best = best_config(df_train, cfg, show_progress=show_progress)
	
	if not train_best:
		return {
			"train_best": {},
			"test_metrics": {},
			"train_sharpe": np.nan,
			"test_sharpe": np.nan,
			"sharpe_degradation": np.nan
		}
	
	train_sharpe = train_best['sharpe_ratio']
	print(f"Best training Sharpe: {round(train_sharpe, 2)}")
	print(f"Optimal params: lookback={int(train_best['lookback'])}, "
	      f"entry_z={round(train_best['entry_z'], 2)}, exit_z={round(train_best['exit_z'], 2)}\n")
	
	# Test on out-of-sample data
	print("Validating on test data...")
	test_result = _single_run(
		df_test,
		lookback=int(train_best['lookback']),
		entry_z=train_best['entry_z'],
		exit_z=train_best['exit_z']
	)
	
	if test_result is None:
		return {
			"train_best": train_best,
			"test_metrics": {},
			"train_sharpe": train_sharpe,
			"test_sharpe": np.nan,
			"sharpe_degradation": np.nan
		}
	
	test_sharpe = test_result['sharpe_ratio']
	degradation = ((train_sharpe - test_sharpe) / abs(train_sharpe) * 100) if train_sharpe != 0 else np.nan
	
	print(f"Test Sharpe: {round(test_sharpe, 2)}")
	print(f"Sharpe degradation: {round(degradation, 1)}%\n")
	
	return {
		"train_best": train_best,
		"test_metrics": test_result,
		"train_sharpe": train_sharpe,
		"test_sharpe": test_sharpe,
		"sharpe_degradation": degradation
	}


def robustness_analysis(df_prices: pd.DataFrame, cfg: GridSearchConfig, 
                       n_periods: int = 3, show_progress: bool = True) -> pd.DataFrame:
	"""Analyse parameter robustness across multiple time periods.
	
	robustness_analysis splits the data into n consecutive periods and
	identifies the best parameters for each period. Robust parameters
	should perform well consistently across different market regimes.
	
	Args:
		df_prices : pd.DataFrame
			DataFrame containing two columns of historical price data.
		cfg : GridSearchConfig
			Configuration object defining parameter ranges and quality filters.
		n_periods : int, default = 3
			Number of time periods to split data into.
		show_progress : bool, default = True
			Whether to display progress bar during optimisation.
	
	Returns:
		pd.DataFrame
			DataFrame with one row per period containing:
				- period: Period number (1 to n_periods)
				- start_date: Start date of period
				- end_date: End date of period
				- lookback: Optimal lookback for this period
				- entry_z: Optimal entry threshold
				- exit_z: Optimal exit threshold
				- sharpe_ratio: Sharpe ratio achieved
				- total_return: Total return achieved
	
	Example:
		>>> config = GridSearchConfig(
		...     lookbacks=[30, 60, 90],
		...     entry_zs=[1.5, 2.0, 2.5],
		...     exit_zs=[0.25, 0.5, 0.75]
		... )
		>>> results = robustness_analysis(df_prices, config, n_periods=4)
		>>> print(results[['period', 'lookback', 'entry_z', 'sharpe_ratio']])
	
	Notes:
		- Consistent parameters across periods suggest robustness
		- Highly variable parameters indicate regime-dependent strategy
		- Use results to identify stable parameter regions
	"""
	if n_periods < 2:
		raise ValueError("n_periods must be at least 2")
	
	period_size = len(df_prices) // n_periods
	results = []
	
	for i in range(n_periods):
		start_idx = i * period_size
		end_idx = (i + 1) * period_size if i < n_periods - 1 else len(df_prices)
		
		df_period = df_prices.iloc[start_idx:end_idx].copy()
		
		print(f"\n{'=' * 70}")
		print(f"Period {i + 1}/{n_periods}: {len(df_period)} rows")
		print(f"{'=' * 70}")
		
		best = best_config(df_period, cfg, show_progress=show_progress)
		
		if best:
			results.append({
				"period": i + 1,
				"start_idx": start_idx,
				"end_idx": end_idx,
				"n_rows": len(df_period),
				"lookback": int(best['lookback']),
				"entry_z": best['entry_z'],
				"exit_z": best['exit_z'],
				"sharpe_ratio": best['sharpe_ratio'],
				"total_return": best['total_return'],
				"max_drawdown": best['max_drawdown'],
				"num_trades": int(best['num_trades'])
			})
	
	df_results = pd.DataFrame(results)
	
	if not df_results.empty:
		print(f"\n{'=' * 70}")
		print("ROBUSTNESS SUMMARY")
		print(f"{'=' * 70}")
		print(f"Lookback range:  {df_results['lookback'].min()} - {df_results['lookback'].max()}")
		print(f"Entry Z range:   {round(df_results['entry_z'].min(), 2)} - {round(df_results['entry_z'].max(), 2)}")
		print(f"Exit Z range:    {round(df_results['exit_z'].min(), 2)} - {round(df_results['exit_z'].max(), 2)}")
		print(f"Sharpe range:    {round(df_results['sharpe_ratio'].min(), 2)} - {round(df_results['sharpe_ratio'].max(), 2)}")
		print(f"Mean Sharpe:     {round(df_results['sharpe_ratio'].mean(), 2)}")
		print(f"Sharpe std dev:  {round(df_results['sharpe_ratio'].std(), 2)}")
	
	return df_results


def transaction_cost_analysis(df_prices: pd.DataFrame, cfg: GridSearchConfig, 
                              cost_bps_range: List[float] = [0, 5, 10, 20, 50], 
                              show_progress: bool = True) -> pd.DataFrame:
	"""Analyse sensitivity of optimal parameters to transaction costs.
	
	transaction_cost_analysis evaluates how different transaction cost levels
	affect the optimal parameter selection and strategy profitability. Higher
	costs typically favour lower-frequency strategies with wider thresholds.
	
	Args:
		df_prices : pd.DataFrame
			DataFrame containing two columns of historical price data.
		cfg : GridSearchConfig
			Configuration object defining parameter ranges and quality filters.
		cost_bps_range : List[float], default = [0, 5, 10, 20, 50]
			Transaction costs to test in basis points (1 bps = 0.01%).
		show_progress : bool, default = True
			Whether to display progress bar during optimisation.
	
	Returns:
		pd.DataFrame
			DataFrame with one row per cost level containing:
				- cost_bps: Transaction cost in basis points
				- lookback: Optimal lookback at this cost level
				- entry_z: Optimal entry threshold
				- exit_z: Optimal exit threshold
				- sharpe_ratio: Sharpe ratio after costs
				- total_return: Total return after costs
				- num_trades: Number of trades
				- cost_drag: Total cost impact on returns
	
	Example:
		>>> config = GridSearchConfig(
		...     lookbacks=[30, 60, 90],
		...     entry_zs=[1.5, 2.0, 2.5],
		...     exit_zs=[0.25, 0.5, 0.75]
		... )
		>>> results = transaction_cost_analysis(df_prices, config)
		>>> print(results[['cost_bps', 'num_trades', 'sharpe_ratio']])
	
	Notes:
		- Cost drag = num_trades * 2 * cost_bps / 10000
		- Strategies should favour wider thresholds as costs increase
		- Break-even cost is where Sharpe ratio becomes zero
	"""
	results = []
	
	# First get baseline results without costs
	print("Running baseline optimisation (0 bps cost)...")
	baseline_results = grid_search(df_prices, cfg, show_progress=show_progress)
	
	if baseline_results.empty:
		print("No valid configurations found in baseline.")
		return pd.DataFrame()
	
	for cost_bps in cost_bps_range:
		print(f"\n{'=' * 70}")
		print(f"Analysing with {cost_bps} bps transaction cost")
		print(f"{'=' * 70}")
		
		# Apply transaction costs to baseline results
		cost_fraction = cost_bps / 10000.0  # Convert bps to fraction
		results_with_cost = baseline_results.copy()
		
		# Cost per trade = 2 * cost_fraction (entry + exit)
		# Total cost drag = num_trades * 2 * cost_fraction
		results_with_cost['cost_drag'] = results_with_cost['num_trades'] * 2 * cost_fraction
		results_with_cost['total_return_after_cost'] = results_with_cost['total_return'] - results_with_cost['cost_drag']
		
		# Recalculate Sharpe with costs (approximate)
		# Sharpe = mean_return / std_return, costs reduce mean proportionally
		results_with_cost['sharpe_ratio_after_cost'] = np.where(
			results_with_cost['total_return'] != 0,
			results_with_cost['sharpe_ratio'] * (results_with_cost['total_return_after_cost'] / results_with_cost['total_return']),
			0
		)
		
		# Re-sort by Sharpe after costs
		results_with_cost = results_with_cost.sort_values(
			by=['sharpe_ratio_after_cost', 'total_return_after_cost'],
			ascending=[False, False]
		).reset_index(drop=True)
		
		if not results_with_cost.empty:
			best = results_with_cost.iloc[0]
			results.append({
				"cost_bps": cost_bps,
				"lookback": int(best['lookback']),
				"entry_z": best['entry_z'],
				"exit_z": best['exit_z'],
				"sharpe_ratio": best['sharpe_ratio_after_cost'],
				"total_return": best['total_return_after_cost'],
				"num_trades": int(best['num_trades']),
				"cost_drag": best['cost_drag']
			})
			
			print(f"Best config: lookback={int(best['lookback'])}, "
			      f"entry_z={round(best['entry_z'], 2)}, exit_z={round(best['exit_z'], 2)}")
			print(f"Sharpe after cost: {round(best['sharpe_ratio_after_cost'], 2)}")
			print(f"Trades: {int(best['num_trades'])}, Cost drag: {round(best['cost_drag'], 4)}")
	
	df_results = pd.DataFrame(results)
	
	if not df_results.empty:
		print(f"\n{'=' * 70}")
		print("TRANSACTION COST SENSITIVITY SUMMARY")
		print(f"{'=' * 70}")
		print(df_results.to_string(index=False))
	
	return df_results


def identify_stable_regions(results: pd.DataFrame, top_n: int = 10, 
                           tolerance: Dict[str, float] = None) -> Dict[str, Any]:
	"""Identify stable parameter regions from grid search results.
	
	identify_stable_regions analyses the top-performing configurations to
	find clusters of similar parameters. Stable regions indicate robust
	parameter choices that aren't overly sensitive to small changes.
	
	Args:
		results : pd.DataFrame
			Grid search results from grid_search() function.
		top_n : int, default = 10
			Number of top configurations to analyse.
		tolerance : Dict[str, float], optional
			Maximum variation to consider parameters "stable".
			Default: {"lookback": 15, "entry_z": 0.5, "exit_z": 0.25}
	
	Returns:
		Dict[str, Any]
			Dictionary containing:
				- lookback_range: (min, max) of top configs
				- entry_z_range: (min, max) of top configs
				- exit_z_range: (min, max) of top configs
				- lookback_stable: True if range within tolerance
				- entry_z_stable: True if range within tolerance
				- exit_z_stable: True if range within tolerance
				- overall_stable: True if all parameters stable
				- median_params: Median values of top configs
	
	Example:
		>>> results = grid_search(df_prices, config)
		>>> stability = identify_stable_regions(results, top_n=10)
		>>> if stability['overall_stable']:
		...     print("Parameters are robust!")
		...     print(f"Use median: {stability['median_params']}")
	
	Notes:
		- Stable regions suggest parameters generalise well
		- Unstable regions indicate overfitting or regime sensitivity
		- Consider using median of stable region as final parameters
	"""
	if tolerance is None:
		tolerance = {"lookback": 15, "entry_z": 0.5, "exit_z": 0.25}
	
	if results.empty:
		return {
			"lookback_range": (np.nan, np.nan),
			"entry_z_range": (np.nan, np.nan),
			"exit_z_range": (np.nan, np.nan),
			"lookback_stable": False,
			"entry_z_stable": False,
			"exit_z_stable": False,
			"overall_stable": False,
			"median_params": {}
		}
	
	# Get top N configurations
	top_configs = results.head(min(top_n, len(results)))
	
	# Calculate ranges
	lookback_min = top_configs['lookback'].min()
	lookback_max = top_configs['lookback'].max()
	entry_z_min = top_configs['entry_z'].min()
	entry_z_max = top_configs['entry_z'].max()
	exit_z_min = top_configs['exit_z'].min()
	exit_z_max = top_configs['exit_z'].max()
	
	# Check stability
	lookback_stable = (lookback_max - lookback_min) <= tolerance['lookback']
	entry_z_stable = (entry_z_max - entry_z_min) <= tolerance['entry_z']
	exit_z_stable = (exit_z_max - exit_z_min) <= tolerance['exit_z']
	overall_stable = lookback_stable and entry_z_stable and exit_z_stable
	
	# Calculate medians
	median_params = {
		"lookback": int(top_configs['lookback'].median()),
		"entry_z": float(top_configs['entry_z'].median()),
		"exit_z": float(top_configs['exit_z'].median())
	}
	
	return {
		"lookback_range": (int(lookback_min), int(lookback_max)),
		"entry_z_range": (float(entry_z_min), float(entry_z_max)),
		"exit_z_range": (float(exit_z_min), float(exit_z_max)),
		"lookback_stable": lookback_stable,
		"entry_z_stable": entry_z_stable,
		"exit_z_stable": exit_z_stable,
		"overall_stable": overall_stable,
		"median_params": median_params,
		"top_n_analysed": len(top_configs)
	}
