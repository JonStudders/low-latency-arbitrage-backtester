# experiments/run_data_utils_test.py

## Imports
import sys
from pathlib import Path
import pandas as pd

# Allow imports from /src when running this script directly
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_utils import download_data


## Functions
def main():
  """
  Manual batch test for the data download utility.

  This script downloads multiple asset pairs from Yahoo Finance,
  checks that the data looks valid, and saves each pair's prices
  to a separate CSV file under /data.

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
    print(f"Downloading data for {ticker_a} and {ticker_b}.")

    # Download the aligned price data.
    df = download_data(ticker_a, ticker_b)

    # Make sure the data is valid.
    if df.empty:
      print(f"No data returned for {ticker_a} and {ticker_b}.")
      continue # Skip Row.

    print(f"Downloaded {len(df)} rows.")

    # Save to /data/{ticker_a}_{ticker_b}.csv
    filename = f"{ticker_a.replace('=','')}_{ticker_b.replace('=','')}.csv"
    save_path = Path("data") / filename
    df.to_csv(save_path, index=True)

    print(f"Saved to {save_path.resolve()}")

  # Confirm all the pairs have been downloaded.
  print("All downloads complete.")

if __name__ == "__main__":
  main()
