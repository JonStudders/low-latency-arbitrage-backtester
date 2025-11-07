# tests/test_metrics.py

## Imports
import pytest
import pandas as pd
import numpy as np
from src.metrics import calculate_performance_metrics


## Tests for calculate_performance_metrics()

def test_calculate_performance_metrics_returns_expected_keys():
	"""
	Ensure calculate_performance_metrics() returns all expected metric keys.
	"""
	# Arrange: Create a simple backtest result
	df = pd.DataFrame({
		"pnl": [0, 0.01, -0.005, 0.02, 0.01],
		"cum_pnl": [0, 0.01, 0.005, 0.025, 0.035],
		"signal": [0, 1, 1, 1, 0]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Verify all expected keys are present
	expected_keys = {
		"total_return", "sharpe_ratio", "sortino_ratio", "max_drawdown", 
		"win_rate", "num_trades", "turnover", "avg_win", "avg_loss", "profit_factor"
	}
	assert set(metrics.keys()) == expected_keys, "Missing or extra metric keys"


def test_calculate_performance_metrics_raises_for_missing_columns():
	"""
	Ensure ValueError is raised if required columns are missing.
	"""
	# Arrange: Create an invalid DataFrame without required columns
	df = pd.DataFrame({"pnl": [0.01, 0.02]})

	# Act & Assert: Expect ValueError when columns are missing
	with pytest.raises(ValueError):
		calculate_performance_metrics(df)


def test_total_return_calculation():
	"""
	Verify total return equals final cumulative PnL.
	"""
	# Arrange: Create a DataFrame with known cumulative PnL
	df = pd.DataFrame({
		"pnl": [0, 0.05, 0.03, -0.02],
		"cum_pnl": [0, 0.05, 0.08, 0.06],
		"signal": [1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Total return should equal final cum_pnl
	assert np.isclose(metrics["total_return"], 0.06), \
		f"Expected total_return=0.06, got {metrics['total_return']}"


def test_sharpe_ratio_calculation():
	"""
	Verify Sharpe ratio is calculated correctly.
	"""
	# Arrange: Create a DataFrame with consistent positive returns
	pnl_values = [0.01] * 10  # Consistent 1% daily returns
	df = pd.DataFrame({
		"pnl": pnl_values,
		"cum_pnl": np.cumsum(pnl_values),
		"signal": [1] * 10
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Sharpe ratio should be very high for consistent returns
	# With zero std, Sharpe should be NaN (we handle this case)
	assert np.isnan(metrics["sharpe_ratio"]) or metrics["sharpe_ratio"] > 0, \
		"Sharpe ratio should be NaN or positive for consistent returns"


def test_sortino_ratio_calculation():
	"""
	Verify Sortino ratio is calculated correctly (downside risk only).
	"""
	# Arrange: Create a DataFrame with mixed returns
	df = pd.DataFrame({
		"pnl": [0, 0.02, -0.01, 0.03, -0.005, 0.01],
		"cum_pnl": [0, 0.02, 0.01, 0.04, 0.035, 0.045],
		"signal": [1, 1, 1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Sortino ratio should be calculated
	assert not np.isnan(metrics["sortino_ratio"]), \
		"Sortino ratio should be calculated for mixed returns"
	# Sortino should be higher than Sharpe (only penalises downside)
	assert metrics["sortino_ratio"] >= metrics["sharpe_ratio"], \
		"Sortino ratio should be >= Sharpe ratio"


def test_max_drawdown_calculation():
	"""
	Verify maximum drawdown captures worst peak-to-trough decline.
	"""
	# Arrange: Create a DataFrame with known drawdown pattern
	# Peak at 0.10, trough at 0.02, drawdown = -0.08
	df = pd.DataFrame({
		"pnl": [0, 0.05, 0.05, -0.03, -0.05, 0.02],
		"cum_pnl": [0, 0.05, 0.10, 0.07, 0.02, 0.04],
		"signal": [1, 1, 1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Max drawdown should be -0.08 (from 0.10 to 0.02)
	assert np.isclose(metrics["max_drawdown"], -0.08), \
		f"Expected max_drawdown=-0.08, got {metrics['max_drawdown']}"


def test_win_rate_calculation():
	"""
	Verify win rate is calculated correctly.
	"""
	# Arrange: Create a DataFrame with 3 wins and 2 losses (60% win rate)
	df = pd.DataFrame({
		"pnl": [0, 0.01, 0.02, -0.01, 0.01, -0.005],
		"cum_pnl": [0, 0.01, 0.03, 0.02, 0.03, 0.025],
		"signal": [0, 1, 1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Win rate should be 3/5 = 0.60
	assert np.isclose(metrics["win_rate"], 0.60), \
		f"Expected win_rate=0.60, got {metrics['win_rate']}"


def test_num_trades_calculation():
	"""
	Verify number of trades counts position changes correctly.
	"""
	# Arrange: Create a DataFrame with 3 position changes
	# 0 -> 1 (trade 1), 1 -> -1 (trade 2), -1 -> 0 (trade 3)
	df = pd.DataFrame({
		"pnl": [0, 0.01, 0.02, -0.01, 0.01, 0.005],
		"cum_pnl": [0, 0.01, 0.03, 0.02, 0.03, 0.035],
		"signal": [0, 1, 1, -1, -1, 0]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Should count 3 position changes
	assert metrics["num_trades"] == 3, \
		f"Expected num_trades=3, got {metrics['num_trades']}"


def test_turnover_calculation():
	"""
	Verify turnover measures average daily position change.
	"""
	# Arrange: Create a DataFrame with known position changes
	# Changes: 0->1 (1), 1->1 (0), 1->-1 (2), -1->-1 (0), -1->0 (1)
	# Average turnover = (1 + 0 + 2 + 0 + 1) / 5 = 0.8
	df = pd.DataFrame({
		"pnl": [0, 0.01, 0.02, -0.01, 0.01, 0.005],
		"cum_pnl": [0, 0.01, 0.03, 0.02, 0.03, 0.035],
		"signal": [0, 1, 1, -1, -1, 0]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Turnover should be calculated
	assert metrics["turnover"] > 0, \
		f"Expected positive turnover, got {metrics['turnover']}"


def test_avg_win_and_avg_loss_calculation():
	"""
	Verify average win and average loss are calculated correctly.
	"""
	# Arrange: Create a DataFrame with known wins and losses
	# Wins: 0.02, 0.04 (avg = 0.03)
	# Losses: -0.01, -0.03 (avg = -0.02)
	df = pd.DataFrame({
		"pnl": [0, 0.02, -0.01, 0.04, -0.03],
		"cum_pnl": [0, 0.02, 0.01, 0.05, 0.02],
		"signal": [1, 1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Verify average win and loss
	assert np.isclose(metrics["avg_win"], 0.03), \
		f"Expected avg_win=0.03, got {metrics['avg_win']}"
	assert np.isclose(metrics["avg_loss"], -0.02), \
		f"Expected avg_loss=-0.02, got {metrics['avg_loss']}"


def test_profit_factor_calculation():
	"""
	Verify profit factor is calculated correctly.
	"""
	# Arrange: Create a DataFrame with known profit factor
	# Gross profit: 0.05 + 0.03 = 0.08
	# Gross loss: 0.02 + 0.01 = 0.03
	# Profit factor: 0.08 / 0.03 = 2.67
	df = pd.DataFrame({
		"pnl": [0, 0.05, -0.02, 0.03, -0.01],
		"cum_pnl": [0, 0.05, 0.03, 0.06, 0.05],
		"signal": [1, 1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Profit factor should be approximately 2.67
	expected_pf = 0.08 / 0.03
	assert np.isclose(metrics["profit_factor"], expected_pf, atol=0.01), \
		f"Expected profit_factor≈{expected_pf}, got {metrics['profit_factor']}"


def test_empty_dataframe_returns_default_metrics():
	"""
	Ensure empty DataFrame returns sensible default values.
	"""
	# Arrange: Create an empty DataFrame
	df = pd.DataFrame({"pnl": [], "cum_pnl": [], "signal": []})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Should return default values without crashing
	assert metrics["total_return"] == 0.0, "Empty DataFrame should have zero return"
	assert metrics["num_trades"] == 0, "Empty DataFrame should have zero trades"
	assert np.isnan(metrics["sharpe_ratio"]), "Empty DataFrame should have NaN Sharpe"
	assert np.isnan(metrics["sortino_ratio"]), "Empty DataFrame should have NaN Sortino"


def test_all_winning_trades_profit_factor():
	"""
	Verify profit factor is infinity when there are no losses.
	"""
	# Arrange: Create a DataFrame with only winning trades
	df = pd.DataFrame({
		"pnl": [0, 0.01, 0.02, 0.01],
		"cum_pnl": [0, 0.01, 0.03, 0.04],
		"signal": [1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Profit factor should be infinity (no losses)
	assert np.isinf(metrics["profit_factor"]), \
		"Profit factor should be infinity when there are no losses"


def test_all_losing_trades_profit_factor():
	"""
	Verify profit factor is zero when there are no wins.
	"""
	# Arrange: Create a DataFrame with only losing trades
	df = pd.DataFrame({
		"pnl": [0, -0.01, -0.02, -0.01],
		"cum_pnl": [0, -0.01, -0.03, -0.04],
		"signal": [1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Profit factor should be 0.0 (no wins, only losses)
	assert metrics["profit_factor"] == 0.0, \
		"Profit factor should be 0.0 when there are no wins"


def test_win_rate_with_no_active_positions():
	"""
	Verify win rate is zero when there are no active positions.
	"""
	# Arrange: Create a DataFrame with all flat signals
	df = pd.DataFrame({
		"pnl": [0, 0, 0, 0],
		"cum_pnl": [0, 0, 0, 0],
		"signal": [0, 0, 0, 0]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Win rate should be 0 when no positions are taken
	assert metrics["win_rate"] == 0.0, \
		"Win rate should be 0 when there are no active positions"


def test_sortino_ratio_with_no_downside():
	"""
	Verify Sortino ratio is NaN when there are no negative returns.
	"""
	# Arrange: Create a DataFrame with only positive returns
	df = pd.DataFrame({
		"pnl": [0, 0.01, 0.02, 0.01],
		"cum_pnl": [0, 0.01, 0.03, 0.04],
		"signal": [1, 1, 1, 1]
	})

	# Act: Calculate metrics
	metrics = calculate_performance_metrics(df)

	# Assert: Sortino ratio should be NaN (no downside volatility)
	assert np.isnan(metrics["sortino_ratio"]), \
		"Sortino ratio should be NaN when there are no negative returns"
