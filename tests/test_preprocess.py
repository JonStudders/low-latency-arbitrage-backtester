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
  df = pd.DataFrame({
    "A": np.arange(100, 110),
    "B": np.arange(99, 109)
  })
  result = prepare_spread(df, lookback=3)
  for col in ["spread", "spread_mean", "spread_std", "zscore"]:
    assert col in result.columns


def test_prepare_spread_computes_valid_zscores():
  """
  Ensure z-scores are computed and not NaN.
  """
  df = pd.DataFrame({
    "A": np.linspace(100, 109, 20),
    "B": np.linspace(99, 108, 20)
  })
  result = prepare_spread(df, lookback=5)
  z = result["zscore"]
  assert np.isfinite(z).all(), "Z-scores should be finite numeric values"


def test_prepare_spread_raises_for_invalid_columns():
  """
  Ensure function handles an incorrect number of columns in the DataFrame.
  """
  df = pd.DataFrame({
    "A": np.arange(5),
    "B": np.arange(5),
    "C": np.arange(5)
  })
  with pytest.raises(ValueError):
    prepare_spread(df)


def test_prepare_spread_handles_missing_data_gracefully():
  """
  Ensure NaN values are being dropped.
  """
  df = pd.DataFrame({
    "A": [1, 2, 3, 4, 5, np.nan, 7, 8, 9, 10],
    "B": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
  })
  result = prepare_spread(df, lookback=3)
  assert not result.isna().any().any(), "Result should not contain NaNs after dropna()"


def test_prepare_spread_respects_lookback_window():
  """
  Ensure the number of NaN rows dropped aligns with no missing rows.
  """
  df = pd.DataFrame({
    "A": np.arange(10),
    "B": np.arange(10)
  })
  result = prepare_spread(df, lookback=5)
  expected_rows = len(df) - (5 - 1)
  assert len(result) == expected_rows, "Result should have the correct number of rows after dropping NaNs."