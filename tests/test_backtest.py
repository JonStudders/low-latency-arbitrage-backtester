# tests/test_backtest.py

## Imports
import pytest
import pandas as pd
import numpy as np
from src.backtest import run_backtest


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
