# src/preprocess.py

## Imports
import pandas as pd
import numpy as np

## Functions
def prepare_spread(df: pd.DataFrame, lookback: int = 60) -> pd.DataFrame:
  """
  Compute hedge-ratio-adjusted spread, rolling mean, std, and z-score between two assets.

  prepare_spread estimates a rolling hedge ratio (β) between the two assets to
  normalise scale differences and better capture the true relative movement.
  It then computes the price difference (spread) between two assets,
  along with the rolling average and a standardised "z-score" that indicates
  how unusual the current spread is compared to its recent history.

  Args:
    df : pd.DataFrame
      A pandas DataFrame with two columns, one for each asset.
    lookback : int, default = 60
      The number of past data points to use when calculating mean and std.

  Returns:
    pd.DataFrame
      The original DataFrame with five new columns: beta, spread, spread_mean, spread_std, and zscore.

  Example:
    >>> df = pd.DataFrame({
    ...     'SPY': [100, 102, 104, 106, 108],
    ...     'QQQ': [200, 204, 208, 212, 216]
    ... })
    >>> result = prepare_spread(df, lookback=3)
    >>> 'zscore' in result.columns
    True
  """
  # Validate that we have exactly two columns for spread calculation
  if df.shape[1] != 2:
    raise ValueError("Expected exactly two columns for spread calculation.")

  # Handle empty DataFrame gracefully
  if df.empty:
    return df

  a, b = df.columns

  # Make a copy so we don't modify the original data
  df = df.copy()

  # Calculate rolling hedge ratio (beta) to normalise scale differences
  # Beta tells us how much Asset A moves relative to Asset B
  cov = df[a].rolling(window=lookback).cov(df[b])
  var = df[b].rolling(window=lookback).var()
  df["beta"] = cov / var

  # Fill initial NaN values in beta by using the first valid calculation
  # This ensures we have a hedge ratio for all rows after the warmup period
  df["beta"] = df["beta"].bfill()

  # Calculate the adjusted spread using the hedge ratio
  # This removes the scale difference between the two assets
  df["spread"] = df[a] - df["beta"] * df[b]

  # Calculate rolling statistics for the spread
  df["spread_mean"] = df["spread"].rolling(window=lookback).mean()
  df["spread_std"] = df["spread"].rolling(window=lookback).std()

  # Normalise the spread into a z-score
  # Replace zero std with NaN to avoid division by zero
  df["zscore"] = (df["spread"] - df["spread_mean"]) / df["spread_std"].replace(0, np.nan)
  
  # If spread doesn't change (std=0), set z-score to 0 rather than NaN
  df["zscore"] = df["zscore"].fillna(0)

  # Remove warmup period where rolling statistics couldn't be calculated
  df = df.dropna(subset=["spread_mean", "spread_std"])

  return df