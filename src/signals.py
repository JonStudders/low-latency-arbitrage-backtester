# src/signals.py

## Imports
import pandas as pd

## Functions
def generate_trade_signals(
  df: pd.DataFrame,
  entry_z: float = 2.0,
  exit_z: float = 0.5,
  column: str = "zscore",
) -> pd.DataFrame:
  """
  Convert z-score of the spread into long/short trading positions.

  generate_trade_signals applies a simple mean reversion logic:
  when the z-score of the spread becomes extreme, we open a trade,
  and when it returns near normal levels, we close the trade.

  Rules:
    - z > +entry_z → short spread (sell first, buy second)
    - z < -entry_z → long spread (buy first, sell second)
    - |z| <= exit_z → flat (no position)

  Args:
    df : pd.DataFrame
      DataFrame containing at least the z-score column.
    entry_z : float, default = 2.0
      Z-score threshold to open a position.
    exit_z : float, default = 0.5
      Z-score threshold to close a position.
    column : str, default = "zscore"
      Column name to use for signal generation.

  Returns:
    pd.DataFrame
      The same DataFrame with an added 'signal' column:
        +1 = long spread
        -1 = short spread
          0 = no position
  """

  if column not in df.columns:
    raise ValueError(f"Required column '{column}' not found in DataFrame.")

  if entry_z <= exit_z:
    raise ValueError("entry_z must be strictly greater than exit_z to avoid chattering.")

  # Handle empty DataFrame gracefully
  if df.empty:
    return df

  # Make a copy so we don't modify the original data
  out = df.copy()

  # Start with no active positions (flat)
  out["signal"] = 0

  # Mark entry points based on extreme z-score values
  out.loc[out[column] > +entry_z, "signal"] = -1  # Short spread when z-score is high
  out.loc[out[column] < -entry_z, "signal"] = +1  # Long spread when z-score is low

  # Keep the current position active until we hit an exit signal
  # This prevents us from closing trades prematurely
  # Replace zeros with NA, forward-fill the non-zero signals, then fill remaining NAs with 0
  out["signal"] = (
    out["signal"]
    .astype('Int64')     # Convert to nullable integer type first
    .replace(0, pd.NA)   # Mark flat periods as NA so they don't block forward-fill
    .ffill()             # Propagate last active signal forward
    .fillna(0)           # Any remaining NAs become flat positions
  )

  # Close all positions when z-score returns to normal levels
  exiting = out[column].abs() <= exit_z
  out.loc[exiting, "signal"] = 0

  # Convert to integer type for consistency
  out["signal"] = out["signal"].astype(int)

  return out
