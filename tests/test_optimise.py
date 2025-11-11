# tests/test_optimise.py

## Imports
import pytest
import pandas as pd
import numpy as np
from src.optimise import grid_search, best_config, GridSearchConfig, _single_run


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
