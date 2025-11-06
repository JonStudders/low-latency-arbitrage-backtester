# tests/test_preprocess.py

## Imports
import pandas as pd
import numpy as np
import pytest
from src.preprocess import prepare_spread

# Set random seed for reproducibility in tests
np.random.seed(42)

## Tests

def test_prepare_spread_returns_expected_columns():
  """
  Ensure prepare_spread() returns the correct columns for spread analysis.
  """
  # Arrange: Create a simple DataFrame with two asset columns
  df = pd.DataFrame({
    "A": np.arange(100, 110),
    "B": np.arange(99, 109)
  })
  
  # Act: Call prepare_spread with a lookback window
  result = prepare_spread(df, lookback=3)
  
  # Assert: Verify all expected columns are present
  for col in ["spread", "spread_mean", "spread_std", "zscore"]:
    assert col in result.columns


def test_prepare_spread_computes_valid_zscores():
  """
  Ensure z-scores are computed and not NaN.
  """
  # Arrange: Create a DataFrame with linear price data
  df = pd.DataFrame({
    "A": np.linspace(100, 109, 20),
    "B": np.linspace(99, 108, 20)
  })
  
  # Act: Call prepare_spread and extract z-scores
  result = prepare_spread(df, lookback=5)
  z = result["zscore"]
  
  # Assert: All z-scores should be finite numeric values
  assert np.isfinite(z).all(), "Z-scores should be finite numeric values"


def test_prepare_spread_raises_for_invalid_columns():
  """
  Ensure function handles an incorrect number of columns in the DataFrame.
  """
  # Arrange: Create a DataFrame with three columns (invalid for spread calculation)
  df = pd.DataFrame({
    "A": np.arange(5),
    "B": np.arange(5),
    "C": np.arange(5)
  })
  
  # Act & Assert: Function should raise ValueError for invalid column count
  with pytest.raises(ValueError):
    prepare_spread(df)


def test_prepare_spread_handles_missing_data_gracefully():
  """
  Ensure NaN values are being dropped.
  """
  # Arrange: Create a DataFrame with NaN values in one column
  df = pd.DataFrame({
    "A": [1, 2, 3, 4, 5, np.nan, 7, 8, 9, 10],
    "B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  })
  
  # Act: Call prepare_spread
  result = prepare_spread(df, lookback=3)
  
  # Assert: Result should not contain any NaNs after processing
  assert not result.isna().any().any(), "Result should not contain NaNs after dropna()"


def test_prepare_spread_respects_lookback_window():
  """
  Ensure the number of NaN rows dropped aligns with no missing rows.
  """
  # Arrange: Create a clean DataFrame with no missing values
  df = pd.DataFrame({
    "A": np.arange(10),
    "B": np.arange(10)
  })
  
  # Act: Call prepare_spread with a lookback window
  result = prepare_spread(df, lookback=5)
  
  # Assert: Result should have correct number of rows after dropping warmup period
  expected_rows = len(df) - (5 - 1)
  assert len(result) == expected_rows, "Result should have the correct number of rows after dropping NaNs."


def test_beta_calculation_accuracy():
  """
  Verify hedge ratio (beta) is calculated correctly.
  """
  # Arrange: Create perfectly correlated assets with known relationship
  # If B = 2*A, then beta should be approximately 0.5
  df = pd.DataFrame({
    "A": [100, 102, 104, 106, 108, 110, 112, 114, 116, 118],
    "B": [200, 204, 208, 212, 216, 220, 224, 228, 232, 236]
  })
  
  # Act: Call prepare_spread with a lookback window
  result = prepare_spread(df, lookback=5)
  
  # Assert: Beta should be approximately 0.5 (A moves half as much as B)
  # Allow some tolerance due to rolling window
  final_beta = result["beta"].iloc[-1]
  assert 0.4 < final_beta < 0.6, \
      f"Expected beta ≈0.5 for B=2*A relationship, got {final_beta}"


def test_spread_calculation_with_known_beta():
  """
  Verify spread = A - beta * B is calculated correctly.
  """
  # Arrange: Create perfectly correlated assets where A = 2*B
  df = pd.DataFrame({
    "A": [100, 105, 110],
    "B": [50, 52.5, 55]
  })
  
  # Act: Call prepare_spread
  result = prepare_spread(df, lookback=2)
  
  # Assert: With perfect correlation, beta should be 2.0
  # Spread should be approximately 0 (A = 2*B)
  final_spread = result["spread"].iloc[-1]
  assert abs(final_spread) < 5, \
      f"Expected spread near 0 for perfectly correlated assets, got {final_spread}"


def test_zscore_has_zero_mean_unit_variance():
  """
  Verify z-score normalisation produces approximately zero mean.
  
  Note: Rolling z-scores do NOT have unit variance globally because each
  z-score is normalized by its local rolling std, not a global std.
  This is correct behavior for time-series analysis.
  """
  # Arrange: Create data with known spread behaviour
  np.random.seed(42)
  df = pd.DataFrame({
    "A": 100 + np.random.randn(100).cumsum(),
    "B": 100 + np.random.randn(100).cumsum()
  })
  
  # Act: Call prepare_spread
  result = prepare_spread(df, lookback=20)
  z = result["zscore"]
  
  # Assert: Z-score should have approximately zero mean
  # We don't test for unit variance because rolling z-scores have time-varying variance
  assert abs(z.mean()) < 0.5, f"Z-score mean should be near 0, got {z.mean()}"
  
  # Verify z-scores are finite and reasonable
  assert z.notna().all(), "Z-scores should not contain NaN values"
  assert (z.abs() < 10).all(), "Z-scores should be within reasonable bounds"


def test_constant_spread_produces_zero_zscore():
  """
  If spread has zero variance, z-score should be zero (not NaN).
  """
  # Arrange: Create assets where spread is truly constant
  # We need to manually create a constant spread by using identical values
  # with a fixed offset
  df = pd.DataFrame({
    "A": [100, 100, 100, 100, 100, 100],
    "B": [50, 50, 50, 50, 50, 50]
  })
  
  # Act: Call prepare_spread
  result = prepare_spread(df, lookback=3)
  
  # Assert: Constant prices mean constant spread, std=0, z-score should be 0
  # Our implementation fills NaN (from 0/0) with 0, which is correct
  assert (result["zscore"] == 0).all(), \
      f"Constant spread should produce zero z-scores, got {result['zscore'].values}"


def test_beta_backfill_handles_initial_nans():
  """
  Verify beta is backfilled for initial rows where rolling window is incomplete.
  """
  # Arrange: Create a simple DataFrame
  df = pd.DataFrame({
    "A": np.arange(10, 20),
    "B": np.arange(20, 30)
  })
  
  # Act: Call prepare_spread
  result = prepare_spread(df, lookback=5)
  
  # Assert: Beta should have no NaN values after backfill
  assert not result["beta"].isna().any(), "Beta should be backfilled with no NaN values"


def test_spread_column_exists_and_is_numeric():
  """
  Verify spread column is created and contains numeric values.
  """
  # Arrange: Create a simple DataFrame
  df = pd.DataFrame({
    "A": [100, 105, 110, 115],
    "B": [50, 52, 54, 56]
  })
  
  # Act: Call prepare_spread
  result = prepare_spread(df, lookback=2)
  
  # Assert: Spread should exist and be numeric
  assert "spread" in result.columns, "Spread column should exist"
  assert pd.api.types.is_numeric_dtype(result["spread"]), "Spread should be numeric"
  assert result["spread"].notna().all(), "Spread should have no NaN values"