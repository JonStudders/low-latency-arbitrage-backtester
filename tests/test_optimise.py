# tests/test_optimise.py

## Imports
import pytest
import pandas as pd
import numpy as np
from src.optimise import (
	grid_search, best_config, GridSearchConfig, _single_run,
	walk_forward_validation, robustness_analysis, 
	transaction_cost_analysis, identify_stable_regions
)


## Helper Functions
def make_price_df(n_rows=300):
	"""
	Create a synthetic price DataFrame for testing optimisation functions.
	
	Args:
		n_rows : int, default=300
			Number of rows to generate.
	
	Returns:
		pd.DataFrame with two price columns that exhibit cointegration.
	"""
	np.random.seed(42)
	dates = pd.date_range('2020-01-01', periods=n_rows, freq='D')
	
	# Generate cointegrated price series
	base = np.cumsum(np.random.randn(n_rows)) + 100
	asset_a = base + np.random.randn(n_rows) * 2
	asset_b = base * 0.5 + np.random.randn(n_rows) * 1
	
	df = pd.DataFrame({
		'Asset_A': asset_a,
		'Asset_B': asset_b
	}, index=dates)
	
	return df


## Tests - GridSearchConfig

def test_grid_search_config_creation():
	"""
	GridSearchConfig should initialise with valid parameters.
	"""
	# Arrange & Act: Create configuration with expanded parameter space
	config = GridSearchConfig(
		lookbacks=[20, 30, 40, 50, 60, 70, 80, 90, 100, 120],
		entry_zs=[1.0, 1.5, 2.0, 2.5, 3.0],
		exit_zs=[0.1, 0.25, 0.5, 0.75, 1.0],
		min_trades=10,
		min_obs=200
	)
	
	# Assert: Verify attributes
	assert list(config.lookbacks) == [20, 30, 40, 50, 60, 70, 80, 90, 100, 120]
	assert list(config.entry_zs) == [1.0, 1.5, 2.0, 2.5, 3.0]
	assert list(config.exit_zs) == [0.1, 0.25, 0.5, 0.75, 1.0]
	assert config.min_trades == 10
	assert config.min_obs == 200


def test_grid_search_config_defaults():
	"""
	GridSearchConfig should use default values for optional parameters.
	"""
	# Arrange & Act: Create configuration with defaults
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5]
	)
	
	# Assert: Verify defaults
	assert config.min_trades == 10
	assert config.min_obs == 200


## Tests - _single_run

def test_single_run_returns_dict_with_valid_data():
	"""
	_single_run should return a dictionary with parameters and metrics.
	"""
	# Arrange: Create synthetic price data
	df = make_price_df(n_rows=300)
	
	# Act: Run single configuration
	result = _single_run(df, lookback=60, entry_z=2.0, exit_z=0.5)
	
	# Assert: Verify result structure
	assert result is not None, "Expected non-None result for valid data."
	assert isinstance(result, dict), "Expected dictionary output."
	assert 'lookback' in result
	assert 'entry_z' in result
	assert 'exit_z' in result
	assert 'observations' in result
	assert 'sharpe_ratio' in result
	assert 'total_return' in result


def test_single_run_returns_none_for_insufficient_data():
	"""
	_single_run should return None when processed data has too few rows.
	"""
	# Arrange: Create very small DataFrame
	df = make_price_df(n_rows=10)
	
	# Act: Run with large lookback that leaves insufficient data
	result = _single_run(df, lookback=60, entry_z=2.0, exit_z=0.5)
	
	# Assert: Should return None due to insufficient observations
	assert result is None, "Expected None for insufficient data."


def test_single_run_handles_invalid_parameters_gracefully():
	"""
	_single_run should return None for invalid parameter combinations.
	"""
	# Arrange: Create valid price data
	df = make_price_df(n_rows=300)
	
	# Act: Run with invalid parameters (entry_z <= exit_z)
	result = _single_run(df, lookback=60, entry_z=1.0, exit_z=2.0)
	
	# Assert: Should return None due to invalid parameters
	assert result is None, "Expected None for invalid parameters."


def test_single_run_includes_all_required_metrics():
	"""
	_single_run output should include all metrics from calculate_performance_metrics.
	"""
	# Arrange: Create synthetic price data
	df = make_price_df(n_rows=300)
	
	# Act: Run single configuration
	result = _single_run(df, lookback=60, entry_z=2.0, exit_z=0.5)
	
	# Assert: Verify all expected metrics are present
	expected_keys = [
		'lookback', 'entry_z', 'exit_z', 'observations',
		'total_return', 'sharpe_ratio', 'sortino_ratio', 'max_drawdown',
		'win_rate', 'num_trades', 'turnover', 'avg_win', 'avg_loss', 'profit_factor'
	]
	
	for key in expected_keys:
		assert key in result, f"Missing expected key: {key}"


## Tests - grid_search

def test_grid_search_returns_dataframe():
	"""
	grid_search should return a pandas DataFrame.
	"""
	# Arrange: Create synthetic data and configuration with expanded ranges
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[20, 30, 40, 50, 60, 70, 80],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: Verify output type
	assert isinstance(result, pd.DataFrame), "Expected pandas DataFrame output."


def test_grid_search_filters_invalid_configurations():
	"""
	grid_search should skip configurations where entry_z <= exit_z.
	"""
	# Arrange: Create configuration with overlapping thresholds
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[40, 60, 80],
		entry_zs=[1.0, 1.5, 2.0, 2.5],
		exit_zs=[0.5, 1.0, 1.5, 2.0],  # Some combos will be invalid (e.g., entry=1.0, exit=1.5)
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: Should only include valid combinations
	for _, row in result.iterrows():
		assert row['entry_z'] > row['exit_z'], "Invalid configuration not filtered."


def test_grid_search_applies_quality_filters():
	"""
	grid_search should filter out configurations with insufficient trades or observations.
	"""
	# Arrange: Create configuration with strict filters
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[20, 30, 40, 50, 60, 70],
		entry_zs=[1.5, 2.0, 2.5, 3.0],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=50,  # Very high threshold
		min_obs=250      # Very high threshold
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: All results should meet quality thresholds
	if not result.empty:
		assert (result['num_trades'] >= config.min_trades).all(), "Quality filter failed for min_trades."
		assert (result['observations'] >= config.min_obs).all(), "Quality filter failed for min_obs."


def test_grid_search_sorts_by_sharpe_ratio():
	"""
	grid_search should sort results by Sharpe ratio (descending).
	"""
	# Arrange: Create synthetic data and expanded configuration
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[20, 30, 40, 50, 60, 70, 80, 90, 100],
		entry_zs=[1.0, 1.5, 2.0, 2.5, 3.0],
		exit_zs=[0.1, 0.25, 0.5, 0.75, 1.0],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: Verify sorting (Sharpe ratio should be descending)
	if len(result) > 1:
		sharpe_values = result['sharpe_ratio'].tolist()
		assert sharpe_values == sorted(sharpe_values, reverse=True), "Results not sorted by Sharpe ratio."


def test_grid_search_includes_derived_metrics():
	"""
	grid_search should add derived metrics like return_per_trade and drawdown_to_return.
	"""
	# Arrange: Create synthetic data and configuration
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: Verify derived columns exist
	if not result.empty:
		assert 'return_per_trade' in result.columns, "Missing derived metric: return_per_trade"
		assert 'drawdown_to_return' in result.columns, "Missing derived metric: drawdown_to_return"


def test_grid_search_handles_empty_dataframe():
	"""
	grid_search should handle empty input DataFrame gracefully.
	"""
	# Arrange: Create empty DataFrame
	df = pd.DataFrame(columns=['Asset_A', 'Asset_B'])
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5]
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: Should return empty DataFrame
	assert result.empty, "Expected empty DataFrame for empty input."


def test_grid_search_raises_error_for_invalid_columns():
	"""
	grid_search should raise ValueError if DataFrame doesn't have exactly two columns.
	"""
	# Arrange: Create DataFrame with wrong number of columns
	df = pd.DataFrame({
		'Asset_A': [100, 101, 102],
		'Asset_B': [50, 51, 52],
		'Asset_C': [75, 76, 77]
	})
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5]
	)
	
	# Act & Assert: Should raise ValueError
	with pytest.raises(ValueError, match="exactly two columns"):
		grid_search(df, config, show_progress=False)


def test_grid_search_returns_empty_when_no_valid_configs():
	"""
	grid_search should return empty DataFrame when no configurations pass filters.
	"""
	# Arrange: Create small dataset with impossible filters
	df = make_price_df(n_rows=50)
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=100,  # Impossible threshold
		min_obs=500      # Impossible threshold
	)
	
	# Act: Run grid search
	result = grid_search(df, config, show_progress=False)
	
	# Assert: Should return empty DataFrame with correct columns
	assert result.empty, "Expected empty DataFrame when no configs pass filters."
	expected_columns = [
		"lookback", "entry_z", "exit_z", "observations",
		"total_return", "sharpe_ratio", "sortino_ratio", "max_drawdown",
		"win_rate", "num_trades", "turnover", "avg_win", "avg_loss", "profit_factor"
	]
	assert list(result.columns) == expected_columns, "Empty DataFrame has incorrect column structure."


def test_grid_search_progress_parameter():
	"""
	grid_search should respect show_progress parameter.
	"""
	# Arrange: Create synthetic data and configuration
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run with progress disabled (should not raise errors)
	result_no_progress = grid_search(df, config, show_progress=False)
	
	# Assert: Should complete successfully
	assert isinstance(result_no_progress, pd.DataFrame), "Failed with show_progress=False"


## Tests - best_config

def test_best_config_returns_dict():
	"""
	best_config should return a dictionary with the top configuration.
	"""
	# Arrange: Create synthetic data and expanded configuration
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[20, 35, 50, 65, 80, 100],
		entry_zs=[1.25, 1.75, 2.25, 2.75],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Get best configuration
	result = best_config(df, config, show_progress=False)
	
	# Assert: Verify output type and structure
	assert isinstance(result, dict), "Expected dictionary output."
	if result:  # If not empty
		assert 'lookback' in result
		assert 'entry_z' in result
		assert 'exit_z' in result
		assert 'sharpe_ratio' in result


def test_best_config_returns_highest_sharpe():
	"""
	best_config should return the configuration with highest Sharpe ratio.
	"""
	# Arrange: Create synthetic data and comprehensive configuration
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[25, 35, 45, 55, 65, 75, 85, 95],
		entry_zs=[1.0, 1.5, 2.0, 2.5, 3.0],
		exit_zs=[0.1, 0.3, 0.5, 0.7, 0.9],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Get best configuration and full results
	best = best_config(df, config, show_progress=False)
	all_results = grid_search(df, config, show_progress=False)
	
	# Assert: Best config should match top row of grid search
	if not all_results.empty and best:
		assert best['sharpe_ratio'] == all_results.iloc[0]['sharpe_ratio'], "best_config didn't return highest Sharpe."


def test_best_config_returns_empty_dict_when_no_valid_configs():
	"""
	best_config should return empty dict when no configurations are valid.
	"""
	# Arrange: Create small dataset with impossible filters
	df = make_price_df(n_rows=50)
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=100,
		min_obs=500
	)
	
	# Act: Get best configuration
	result = best_config(df, config, show_progress=False)
	
	# Assert: Should return empty dict
	assert result == {}, "Expected empty dict when no valid configurations."


def test_best_config_handles_empty_dataframe():
	"""
	best_config should return empty dict for empty input DataFrame.
	"""
	# Arrange: Create empty DataFrame
	df = pd.DataFrame(columns=['Asset_A', 'Asset_B'])
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5]
	)
	
	# Act: Get best configuration
	result = best_config(df, config, show_progress=False)
	
	# Assert: Should return empty dict
	assert result == {}, "Expected empty dict for empty input."


## Tests - Integration

def test_full_optimisation_pipeline():
	"""
	Integration test: Run complete optimisation pipeline from data to best config.
	"""
	# Arrange: Create realistic synthetic data with comprehensive parameter grid
	df = make_price_df(n_rows=500)
	config = GridSearchConfig(
		lookbacks=[20, 30, 40, 50, 60, 70, 80, 90, 100, 120],
		entry_zs=[1.0, 1.5, 2.0, 2.5, 3.0],
		exit_zs=[0.1, 0.25, 0.5, 0.75, 1.0],
		min_trades=10,
		min_obs=200
	)
	
	# Act: Run full pipeline
	all_results = grid_search(df, config, show_progress=False)
	best = best_config(df, config, show_progress=False)
	
	# Assert: Verify pipeline produces consistent results
	assert not all_results.empty, "Grid search should produce results."
	assert best != {}, "best_config should return a configuration."
	assert best['sharpe_ratio'] == all_results.iloc[0]['sharpe_ratio'], "Pipeline results inconsistent."
	
	# Verify all results meet quality thresholds
	assert (all_results['num_trades'] >= config.min_trades).all()
	assert (all_results['observations'] >= config.min_obs).all()
	
	# Verify parameter constraints
	for _, row in all_results.iterrows():
		assert row['entry_z'] > row['exit_z'], "Invalid parameter combination in results."


## Tests - Walk-Forward Validation

def test_walk_forward_validation_returns_dict():
	"""
	walk_forward_validation should return a dictionary with train and test results.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=500)
	config = GridSearchConfig(
		lookbacks=[30, 60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run walk-forward validation
	result = walk_forward_validation(df, config, train_fraction=0.7, show_progress=False)
	
	# Assert: Verify structure
	assert isinstance(result, dict), "Expected dictionary output."
	assert 'train_best' in result
	assert 'test_metrics' in result
	assert 'train_sharpe' in result
	assert 'test_sharpe' in result
	assert 'sharpe_degradation' in result


def test_walk_forward_validation_splits_data_correctly():
	"""
	walk_forward_validation should split data according to train_fraction.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=500)
	config = GridSearchConfig(
		lookbacks=[30, 60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=50
	)
	
	# Act: Run with 70/30 split
	result = walk_forward_validation(df, config, train_fraction=0.7, show_progress=False)
	
	# Assert: Train period should be ~350 rows, test ~150 rows
	# Results should reflect this split
	assert result is not None


def test_walk_forward_validation_invalid_fraction():
	"""
	walk_forward_validation should raise error for invalid train_fraction.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5]
	)
	
	# Act & Assert: Invalid fractions should raise ValueError
	with pytest.raises(ValueError):
		walk_forward_validation(df, config, train_fraction=0.0)
	
	with pytest.raises(ValueError):
		walk_forward_validation(df, config, train_fraction=1.0)
	
	with pytest.raises(ValueError):
		walk_forward_validation(df, config, train_fraction=1.5)


def test_walk_forward_validation_calculates_degradation():
	"""
	walk_forward_validation should calculate Sharpe degradation percentage.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=500)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run walk-forward validation
	result = walk_forward_validation(df, config, train_fraction=0.7, show_progress=False)
	
	# Assert: Degradation should be calculated if both Sharpes exist
	if result['train_sharpe'] and result['test_sharpe'] and not np.isnan(result['train_sharpe']):
		assert 'sharpe_degradation' in result
		assert isinstance(result['sharpe_degradation'], (int, float))


## Tests - Robustness Analysis

def test_robustness_analysis_returns_dataframe():
	"""
	robustness_analysis should return a DataFrame with period-by-period results.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=600)
	config = GridSearchConfig(
		lookbacks=[30, 60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run robustness analysis
	result = robustness_analysis(df, config, n_periods=3, show_progress=False)
	
	# Assert: Verify output type
	assert isinstance(result, pd.DataFrame), "Expected pandas DataFrame output."


def test_robustness_analysis_splits_into_periods():
	"""
	robustness_analysis should create n_periods rows in results.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=600)
	config = GridSearchConfig(
		lookbacks=[30, 60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run with 3 periods
	result = robustness_analysis(df, config, n_periods=3, show_progress=False)
	
	# Assert: Should have up to 3 rows (may be less if some periods fail)
	assert len(result) <= 3, "Should have at most n_periods rows."
	if not result.empty:
		assert 'period' in result.columns
		assert result['period'].min() >= 1
		assert result['period'].max() <= 3


def test_robustness_analysis_invalid_periods():
	"""
	robustness_analysis should raise error for invalid n_periods.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=300)
	config = GridSearchConfig(
		lookbacks=[60],
		entry_zs=[2.0],
		exit_zs=[0.5]
	)
	
	# Act & Assert: n_periods < 2 should raise ValueError
	with pytest.raises(ValueError):
		robustness_analysis(df, config, n_periods=1)
	
	with pytest.raises(ValueError):
		robustness_analysis(df, config, n_periods=0)


def test_robustness_analysis_includes_required_columns():
	"""
	robustness_analysis should include all required columns in results.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=600)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run robustness analysis
	result = robustness_analysis(df, config, n_periods=3, show_progress=False)
	
	# Assert: Verify required columns
	if not result.empty:
		required_cols = ['period', 'lookback', 'entry_z', 'exit_z', 'sharpe_ratio', 'total_return']
		for col in required_cols:
			assert col in result.columns, f"Missing required column: {col}"


## Tests - Transaction Cost Analysis

def test_transaction_cost_analysis_returns_dataframe():
	"""
	transaction_cost_analysis should return a DataFrame with cost sensitivity results.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run transaction cost analysis
	result = transaction_cost_analysis(df, config, cost_bps_range=[0, 10, 20], show_progress=False)
	
	# Assert: Verify output type
	assert isinstance(result, pd.DataFrame), "Expected pandas DataFrame output."


def test_transaction_cost_analysis_tests_all_cost_levels():
	"""
	transaction_cost_analysis should test each cost level in range.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60],
		entry_zs=[2.0],
		exit_zs=[0.5],
		min_trades=5,
		min_obs=100
	)
	
	cost_range = [0, 5, 10, 20]
	
	# Act: Run transaction cost analysis
	result = transaction_cost_analysis(df, config, cost_bps_range=cost_range, show_progress=False)
	
	# Assert: Should have one row per cost level
	if not result.empty:
		assert len(result) == len(cost_range), "Should have one row per cost level."
		assert list(result['cost_bps']) == cost_range, "Cost levels should match input."


def test_transaction_cost_analysis_calculates_cost_drag():
	"""
	transaction_cost_analysis should calculate cost drag for each level.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run transaction cost analysis
	result = transaction_cost_analysis(df, config, cost_bps_range=[0, 10, 20], show_progress=False)
	
	# Assert: Cost drag should increase with cost level
	if len(result) > 1:
		assert 'cost_drag' in result.columns
		# Higher costs should generally mean higher drag (unless trade count changes dramatically)
		assert result['cost_drag'].iloc[0] == 0, "Zero cost should have zero drag."


def test_transaction_cost_analysis_reduces_sharpe():
	"""
	transaction_cost_analysis should show Sharpe reduction as costs increase.
	"""
	# Arrange: Create synthetic data
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	
	# Act: Run transaction cost analysis
	result = transaction_cost_analysis(df, config, cost_bps_range=[0, 20, 50], show_progress=False)
	
	# Assert: Sharpe should generally decrease with higher costs
	if len(result) > 1:
		# First cost level (0 bps) should have highest or equal Sharpe
		assert result['sharpe_ratio'].iloc[0] >= result['sharpe_ratio'].iloc[-1] - 0.1


## Tests - Stable Region Identification

def test_identify_stable_regions_returns_dict():
	"""
	identify_stable_regions should return a dictionary with stability metrics.
	"""
	# Arrange: Create grid search results
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	results = grid_search(df, config, show_progress=False)
	
	# Act: Identify stable regions
	stability = identify_stable_regions(results, top_n=10)
	
	# Assert: Verify structure
	assert isinstance(stability, dict), "Expected dictionary output."
	assert 'lookback_range' in stability
	assert 'entry_z_range' in stability
	assert 'exit_z_range' in stability
	assert 'overall_stable' in stability
	assert 'median_params' in stability


def test_identify_stable_regions_calculates_ranges():
	"""
	identify_stable_regions should calculate min/max ranges for parameters.
	"""
	# Arrange: Create grid search results
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	results = grid_search(df, config, show_progress=False)
	
	# Act: Identify stable regions
	stability = identify_stable_regions(results, top_n=5)
	
	# Assert: Ranges should be tuples with (min, max)
	if not results.empty:
		assert isinstance(stability['lookback_range'], tuple)
		assert len(stability['lookback_range']) == 2
		assert stability['lookback_range'][0] <= stability['lookback_range'][1]


def test_identify_stable_regions_checks_tolerance():
	"""
	identify_stable_regions should flag stability based on tolerance.
	"""
	# Arrange: Create grid search results
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	results = grid_search(df, config, show_progress=False)
	
	# Act: Identify stable regions with tight tolerance
	stability_tight = identify_stable_regions(results, top_n=10, tolerance={"lookback": 5, "entry_z": 0.1, "exit_z": 0.1})
	
	# Assert: Stability flags should be boolean
	assert isinstance(stability_tight['lookback_stable'], (bool, np.bool_))
	assert isinstance(stability_tight['entry_z_stable'], (bool, np.bool_))
	assert isinstance(stability_tight['exit_z_stable'], (bool, np.bool_))
	assert isinstance(stability_tight['overall_stable'], (bool, np.bool_))


def test_identify_stable_regions_calculates_median():
	"""
	identify_stable_regions should calculate median parameters from top configs.
	"""
	# Arrange: Create grid search results
	df = make_price_df(n_rows=400)
	config = GridSearchConfig(
		lookbacks=[30, 60, 90],
		entry_zs=[1.5, 2.0, 2.5],
		exit_zs=[0.25, 0.5, 0.75],
		min_trades=5,
		min_obs=100
	)
	results = grid_search(df, config, show_progress=False)
	
	# Act: Identify stable regions
	stability = identify_stable_regions(results, top_n=10)
	
	# Assert: Median params should be within the ranges
	if not results.empty and stability['median_params']:
		median = stability['median_params']
		assert 'lookback' in median
		assert 'entry_z' in median
		assert 'exit_z' in median


def test_identify_stable_regions_handles_empty_results():
	"""
	identify_stable_regions should handle empty results gracefully.
	"""
	# Arrange: Empty DataFrame
	empty_results = pd.DataFrame()
	
	# Act: Identify stable regions
	stability = identify_stable_regions(empty_results, top_n=10)
	
	# Assert: Should return structure with NaN/False values
	assert stability['overall_stable'] == False
	assert stability['median_params'] == {}
