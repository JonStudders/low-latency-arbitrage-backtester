# experiments/run_signals_test.py

## Imports
import sys
from pathlib import Path
import matplotlib.pyplot as plt

# Allow imports from /src when running directly
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_utils import download_data
from preprocess import prepare_spread
from signals import generate_trade_signals


## Functions
def main(show_graphs: bool = True):
  """
  Manual batch test for the signal generation utility.

  This script downloads multiple asset pairs from Yahoo Finance,
  runs the spread and z-score preprocessing step, then applies
  the signal generation logic to create trading signals based on
  z-score thresholds. The output is saved as a CSV file under /data.

  Args:
    show_graphs : bool, default=True
      Define whether to show z-score and signal graph for each asset pair.

  Pairs tested:
    - BZ=F vs CL=F   (Brent vs WTI crude)
    - GOOGL vs META  (tech equities)
    - SPY vs QQQ     (index ETFs)
    - V vs MA        (payment processors)
  """
  # Define pairs.
  pairs = [
    ("BZ=F", "CL=F"),
    ("GOOGL", "META"),
    ("SPY", "QQQ"),
    ("V", "MA")
  ]

  # Create /data folder if missing.
  Path("data").mkdir(exist_ok=True)

  # Loop through each pair.
  for ticker_a, ticker_b in pairs:
    print(f"Processing {ticker_a} and {ticker_b}.")

    # Download data using data_utils.download_data
    df = download_data(ticker_a, ticker_b)
    if df.empty:
      print(f"No data returned for {ticker_a} and {ticker_b}.")
      continue # Skip row

    print(f"Downloaded {len(df)} rows of data.")

    # Run preparation/computation functions on data downloaded.
    print("Running preprocess functionality.")
    processed = prepare_spread(df, lookback=60)
    if processed.empty:
      print(f"Preprocessing returned no data for {ticker_a} and {ticker_b}. Skipping.")
      continue # Skip row

    print(f"Processed {len(processed)} rows after rolling-window warmup.")

    # Generate trading signals based on z-score thresholds.
    print("Generating trading signals.")
    df_signals = generate_trade_signals(processed, entry_z=2.0, exit_z=0.5)

    # Save to /data/{ticker_a}_{ticker_b}_signals.csv
    filename = f"{ticker_a.replace('=','')}_{ticker_b.replace('=','')}_signals.csv"
    save_path = Path("data") / filename
    df_signals.to_csv(save_path, index=True)
    print(f"Saved signal data to {save_path.resolve()}")

    # Plot z-score and signals using pyplot if enabled.
    if show_graphs:
      # Create a new figure for this asset pair and set window title.
      plt.figure(figsize=(10, 6))
      plt.gcf().canvas.manager.set_window_title(f"{ticker_a}-{ticker_b} Signals")

      # Plot the z-score and signal lines.
      plt.plot(df_signals.index, df_signals["zscore"], label="Z-Score", color="steelblue", linewidth=1.5)
      plt.plot(df_signals.index, df_signals["signal"], label="Signal", color="orange", linewidth=1.5)

      # Add horizontal reference lines. 0 line for the mean,
      # (+-) 2 as typical thresholds for entry/exiting.
      plt.axhline(0, color="black", linewidth=0.8)
      plt.axhline(2, color="tomato", linestyle="--", linewidth=0.8)
      plt.axhline(-2, color="tomato", linestyle="--", linewidth=0.8)

      # Title and labels for context.
      plt.title(f"{ticker_a} vs {ticker_b}  |  Z-Score & Trade Signals", fontsize=12)
      plt.xlabel("Date")
      plt.ylabel("Value")

      # Add legend and a faint grid structure.
      plt.legend(loc="upper right")
      plt.grid(True, linestyle="--", alpha=0.3)
      plt.tight_layout()

      # Display the plot interactively (skipped if SHOW_GRAPHS=False).
      plt.show()

  # Confirm all pairs have been processed.
  print("All signal generation complete.")


if __name__ == "__main__":
  SHOW_GRAPHS = False
  main(show_graphs=SHOW_GRAPHS)
