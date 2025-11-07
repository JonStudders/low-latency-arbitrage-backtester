# tests/test_backtest.py

## Imports
import pytest
import pandas as pd
import numpy as np
from src.backtest import run_backtest, calculate_performance_metrics


## Tests

def test_run_backtest_returns_expected_columns():
  """
  Ensure run_backtest() returns the expected columns for PnL analysis.
  """
  # Arrange: Create a simple DataFrame with spread and signal columns
  df = pd.DataFrame({
    "spread": [10, 11, 10.5, 9.5, 9.8, 10.2],
    "signal": [0, 1, 1, -1, -1, 0]
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Verify that all required columns are present
  for col in ["spread_ret", "pnl", "cum_pnl"]:
    assert col in result.columns, f"Missing column: {col}"


def test_run_backtest_computes_valid_pnl():
  """
  Ensure that profit and loss values are computed correctly.
  """
  # Arrange: Create a deterministic dataset
  df = pd.DataFrame({
    "spread": [10, 11, 10.5, 9.5],
    "signal": [0, 1, 1, 0]
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Check that cumulative PnL equals the sum of PnL
  assert np.isclose(result["cum_pnl"].iloc[-1], result["pnl"].sum()), \
      "Cumulative PnL should equal the sum of incremental PnL."


def test_run_backtest_raises_for_missing_columns():
  """
  Ensure ValueError is raised if required columns are missing.
  """
  # Arrange: Create an invalid DataFrame without signal column
  df = pd.DataFrame({"spread": [10, 11, 12]})

  # Act & Assert: Expect ValueError when columns are missing
  with pytest.raises(ValueError):
    run_backtest(df)


def test_flat_signal_results_in_zero_pnl():
  """
  Ensure a flat (zero) signal produces no profit or loss.
  """
  # Arrange: Create a DataFrame where signal remains flat
  df = pd.DataFrame({
    "spread": [10, 10.2, 10.0, 9.9],
    "signal": [0, 0, 0, 0]
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: PnL and cumulative PnL should remain zero
  assert (result["pnl"] == 0).all(), "Expected zero PnL for flat signals."
  assert (result["cum_pnl"] == 0).all(), "Expected flat cumulative PnL for flat signals."


def test_signal_shift_prevents_lookahead_bias():
  """
  Ensure signals are correctly shifted to prevent look-ahead bias.
  """
  # Arrange: Create a simple test case
  df = pd.DataFrame({
    "spread": [10, 11, 10],
    "signal": [0, 1, 1]
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: The first row should always have zero PnL (no prior signal)
  assert result["pnl"].iloc[0] == 0, "First row PnL should be zero (no prior signal)."


def test_long_position_profits_from_spread_increase():
  """
  Verify long positions (+1) make money when spread increases.
  """
  # Arrange: Create a DataFrame where spread increases consistently
  df = pd.DataFrame({
    "spread": [10.0, 11.0, 12.0],
    "signal": [1, 1, 1]  # Long position throughout
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Long position should profit from spread increase
  assert result["pnl"].iloc[1] > 0, "Long should profit when spread rises"
  assert result["pnl"].iloc[2] > 0, "Long should profit when spread rises"


def test_short_position_profits_from_spread_decrease():
  """
  Verify short positions (-1) make money when spread decreases.
  """
  # Arrange: Create a DataFrame where spread decreases consistently
  df = pd.DataFrame({
    "spread": [12.0, 11.0, 10.0],
    "signal": [-1, -1, -1]  # Short position throughout
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Short position should profit from spread decrease
  assert result["pnl"].iloc[1] > 0, "Short should profit when spread falls"
  assert result["pnl"].iloc[2] > 0, "Short should profit when spread falls"


def test_long_position_loses_from_spread_decrease():
  """
  Verify long positions lose money when spread decreases.
  """
  # Arrange: Create a DataFrame where spread decreases
  df = pd.DataFrame({
    "spread": [12.0, 11.0, 10.0],
    "signal": [1, 1, 1]  # Long position throughout
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Long position should lose when spread falls
  assert result["pnl"].iloc[1] < 0, "Long should lose when spread falls"
  assert result["pnl"].iloc[2] < 0, "Long should lose when spread falls"


def test_position_flip_from_long_to_short():
  """
  Verify PnL calculation when position flips from long to short.
  """
  # Arrange: Create a DataFrame with position transition
  df = pd.DataFrame({
    "spread": [10.0, 11.0, 10.5, 10.0],
    "signal": [1, 1, -1, -1]  # Long → Short transition
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Verify PnL signs at each transition
  # Period 1: long position (signal[0]=1), spread increases → profit
  assert result["pnl"].iloc[1] > 0, "Long should profit from spread increase"
  # Period 2: still long (signal[1]=1), spread decreases → loss
  assert result["pnl"].iloc[2] < 0, "Long should lose from spread decrease"
  # Period 3: now short (signal[2]=-1), spread decreases → profit
  assert result["pnl"].iloc[3] > 0, "Short should profit from spread decrease"


def test_position_entry_from_flat():
  """
  Verify PnL is zero during the period we enter a position.
  """
  # Arrange: Create a DataFrame transitioning from flat to long
  df = pd.DataFrame({
    "spread": [10.0, 11.0, 12.0],
    "signal": [0, 1, 1]  # Flat → Long
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Verify PnL during entry
  # Period 0: no position (first row always zero)
  assert result["pnl"].iloc[0] == 0, "First row should have zero PnL"
  # Period 1: still using signal[0]=0, so no PnL
  assert result["pnl"].iloc[1] == 0, "Entry period should have zero PnL"
  # Period 2: now using signal[1]=1, should have PnL
  assert result["pnl"].iloc[2] != 0, "Should have PnL after entry"


def test_spread_return_calculation():
  """
  Verify spread_ret is calculated as percentage change.
  """
  # Arrange: Create a DataFrame with known spread values
  df = pd.DataFrame({
    "spread": [100.0, 105.0, 100.0],
    "signal": [0, 0, 0]
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Verify spread return calculations
  # First row should be 0 or NaN (no prior spread)
  assert result["spread_ret"].iloc[0] == 0 or pd.isna(result["spread_ret"].iloc[0]), \
      "First spread return should be 0 or NaN"
  # Second row: (105-100)/100 = 0.05
  assert np.isclose(result["spread_ret"].iloc[1], 0.05), \
      f"Expected spread_ret=0.05, got {result['spread_ret'].iloc[1]}"
  # Third row: (100-105)/105 = -0.0476
  assert np.isclose(result["spread_ret"].iloc[2], -0.0476, atol=0.0001), \
      f"Expected spread_ret≈-0.0476, got {result['spread_ret'].iloc[2]}"


def test_pnl_calculation_with_known_values():
  """
  Hand-calculate expected PnL and verify exact match.
  """
  # Arrange: Create a DataFrame with simple values for manual verification
  df = pd.DataFrame({
    "spread": [100.0, 110.0, 105.0],
    "signal": [1, 1, 1]  # Long throughout
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Verify hand-calculated PnL values
  # Period 0: no prior signal → PnL = 0
  assert result["pnl"].iloc[0] == 0, "First period should have zero PnL"
  
  # Period 1: signal[0]=1, spread_ret = (110-100)/100 = 0.10
  # PnL = signal[0] * spread_ret[1] = 1 * 0.10 = 0.10
  assert np.isclose(result["pnl"].iloc[1], 0.10), \
      f"Expected PnL=0.10, got {result['pnl'].iloc[1]}"
  
  # Period 2: signal[1]=1, spread_ret = (105-110)/110 = -0.0454
  # PnL = 1 * -0.0454 = -0.0454
  assert np.isclose(result["pnl"].iloc[2], -0.0454, atol=0.0001), \
      f"Expected PnL≈-0.0454, got {result['pnl'].iloc[2]}"
  
  # Cumulative PnL should be sum of all PnL
  expected_cum_pnl = 0.10 - 0.0454
  assert np.isclose(result["cum_pnl"].iloc[2], expected_cum_pnl, atol=0.0001), \
      f"Expected cum_pnl≈{expected_cum_pnl}, got {result['cum_pnl'].iloc[2]}"


def test_empty_dataframe_handling():
  """
  Ensure empty DataFrame is handled gracefully.
  """
  # Arrange: Create an empty DataFrame
  df = pd.DataFrame({"spread": [], "signal": []})

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Should return empty DataFrame or handle gracefully
  assert result.empty or len(result) == 0, "Empty input should produce empty output"


def test_single_row_dataframe():
  """
  Single row should produce zero PnL (no prior signal).
  """
  # Arrange: Create a single-row DataFrame
  df = pd.DataFrame({
    "spread": [10.0],
    "signal": [1]
  })

  # Act: Run the backtest
  result = run_backtest(df)

  # Assert: Verify single row behaviour
  assert len(result) == 1, "Should return single row"
  assert result["pnl"].iloc[0] == 0, "Single row should have zero PnL"


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
    "total_return", "sharpe_ratio", "max_drawdown", "win_rate",
    "num_trades", "avg_win", "avg_loss", "profit_factor"
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
