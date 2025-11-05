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

  # Make a copy so we don't modify the original data.
  out = df.copy()

  # Start flat (no active trades).
  out["signal"] = 0

  # Entry conditions
  out.loc[out[column] > +entry_z, "signal"] = -1  # short spread, z-score above +entry_z
  out.loc[out[column] < -entry_z, "signal"] = +1  # long spread, z-score below -entry_z

  # Carry forward last active position until exit condition is met.
  out["signal"] = (
    out["signal"]
    .replace(0, pd.NA)
    .ffill()
    .fillna(0)
    .infer_objects(copy=False)
  )

  # Exit trades when z-score returns within the neutral band.
  exiting = out[column].abs() <= exit_z
  out.loc[exiting, "signal"] = 0

  # Ensure dtype is int for consistency.
  out["signal"] = out["signal"].astype(int)

  return out
