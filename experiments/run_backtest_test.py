# experiments/run_backtest_test.py

## Imports
import sys
from pathlib import Path
import matplotlib.pyplot as plt

# Allow imports from /src when running directly
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_utils import download_data
from preprocess import prepare_spread
from signals import generate_trade_signals
from backtest import run_backtest
from metrics import calculate_performance_metrics


## Functions
def main(show_graphs: bool = True):
  """
  Manual batch test for the backtesting module.

  This script runs the full pipeline from downloading historical data,
  preparing spreads and z-scores, generating trading signals, and
  running a backtest to simulate profit and loss. It prints a short
  performance summary for each asset pair and saves the full results
  to CSV files under the /data folder.

  Args:
    show_graphs : bool, default=True
      Define whether to show cumulative PnL graph for each asset pair.

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
    print(f"Running backtest for {ticker_a} and {ticker_b}.")

    # Download data using data_utils.download_data
    df = download_data(ticker_a, ticker_b)
    if df.empty:
      print(f"No data returned for {ticker_a} and {ticker_b}.")
      continue # Skip row

    print(f"Downloaded {len(df)} rows of data.")

    # Run preparation/computation functions on data downloaded.
    print("Running preprocess functionality.")
    df_proc = prepare_spread(df, lookback=60)
    if df_proc.empty:
      print(f"Preprocessing returned no data for {ticker_a} and {ticker_b}. Skipping.")
      continue # Skip row

    print(f"Processed {len(df_proc)} rows after rolling-window warmup.")

    # Generate trading signals based on z-score thresholds.
    print("Generating trading signals.")
    df_signals = generate_trade_signals(df_proc, entry_z=2.0, exit_z=0.5)

    # Run backtest simulation to compute PnL.
    print("Running backtest simulation.")
    df_bt = run_backtest(df_signals)

    # Save to /data/{ticker_a}_{ticker_b}_backtest.csv
    filename = f"{ticker_a.replace('=','')}_{ticker_b.replace('=','')}_backtest.csv"
    save_path = Path("data") / filename
    df_bt.to_csv(save_path, index=True)
    print(f"Saved backtest results to {save_path.resolve()}")

    # Calculate and print performance metrics.
    print("\nPerformance Metrics:")
    print("-" * 50)
    metrics = calculate_performance_metrics(df_bt)
    
    print(f"  Total Return:     {metrics['total_return']:>8.4f}")
    print(f"  Sharpe Ratio:     {metrics['sharpe_ratio']:>8.2f}")
    print(f"  Sortino Ratio:    {metrics['sortino_ratio']:>8.2f}")
    print(f"  Max Drawdown:     {metrics['max_drawdown']:>8.4f}")
    print(f"  Win Rate:         {metrics['win_rate']:>8.2%}")
    print(f"  Num Trades:       {metrics['num_trades']:>8d}")
    print(f"  Turnover:         {metrics['turnover']:>8.4f}")
    print(f"  Avg Win:          {metrics['avg_win']:>8.4f}")
    print(f"  Avg Loss:         {metrics['avg_loss']:>8.4f}")
    print(f"  Profit Factor:    {metrics['profit_factor']:>8.2f}")
    print("-" * 50)

    # Plot cumulative PnL using pyplot if enabled.
    if show_graphs:
      # Create a new figure for this asset pair and set window title.
      plt.figure(figsize=(10, 6))
      plt.gcf().canvas.manager.set_window_title(f"{ticker_a}-{ticker_b} Backtest")

      # Plot the cumulative PnL over time.
      plt.plot(df_bt.index, df_bt["cum_pnl"], label="Cumulative PnL", color="steelblue", linewidth=1.5)

      # Add horizontal reference line at zero.
      plt.axhline(0, color="black", linewidth=0.8)

      # Title and labels for context.
      plt.title(f"{ticker_a} vs {ticker_b}  |  Backtest Results", fontsize=12)
      plt.xlabel("Date")
      plt.ylabel("Cumulative PnL")

      # Add legend and a faint grid structure.
      plt.legend(loc="upper left")
      plt.grid(True, linestyle="--", alpha=0.3)
      plt.tight_layout()

      # Display the plot interactively (skipped if SHOW_GRAPHS=False).
      plt.show()

  # Confirm all pairs have been processed.
  print("All backtests complete.")


if __name__ == "__main__":
  SHOW_GRAPHS = False
  main(show_graphs=SHOW_GRAPHS)
