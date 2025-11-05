# tests/test_preprocess.py

## Imports
import pandas as pd
import numpy as np
import pytest
from src.preprocess import prepare_spread

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