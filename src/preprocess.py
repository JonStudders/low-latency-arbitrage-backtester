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
      The original dataframe with four new columns: beta, spread, spread_mean, spread_std, and zscore.
  """
  # Check we have exactly two columns.
  if df.shape[1] != 2:
    raise ValueError("Expected exactly two columns for spread calculation.")

  a, b = df.columns

  # Make a copy so we don't modify the original.
  df = df.copy()

  # Rolling hedge ratio
  cov = df[a].rolling(window=lookback).cov(df[b])
  var = df[b].rolling(window=lookback).var()
  df["beta"] = cov / var

  # Backfill NaNs.
  df["beta"] = df["beta"].bfill()

  # Calculate spread
  df["spread"] = df[a] - df["beta"] * df[b]

  # Calculate rolling average (mean).
  df["spread_mean"] = df["spread"].rolling(window=lookback).mean()

  # Calculate rolling std.
  df["spread_std"] = df["spread"].rolling(window=lookback).std()

  # Calculate z-score, replace zero std with NaN to avoid division by zero.
  df["zscore"] = (df["spread"] - df["spread_mean"]) / df["spread_std"].replace(0, np.nan)
  
  # If spread doesn't change, set z-score to 0.
  df["zscore"] = df["zscore"].fillna(0)

  # Drop the first few rows where rolling stats could not be calculated. (Warmup period)
  df = df.dropna(subset=["spread_mean", "spread_std"])

  return df