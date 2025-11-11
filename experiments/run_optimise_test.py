# experiments/run_optimise_test.py

## Imports
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Allow imports from /src when running directly
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from data_utils import download_data
from optimise import grid_search, best_config, GridSearchConfig


## Functions
def main(show_graphs: bool = True):
	"""
	Manual batch test for the parameter optimisation module.

	This script runs grid search optimisation across multiple asset pairs
	to identify optimal parameter combinations for lookback windows, entry
	thresholds, and exit thresholds. It prints performance summaries and
	optionally generates heatmap visualisations of the parameter space.

	Args:
		show_graphs : bool, default=True
			Whether to display heatmap visualisations for each asset pair.

	Pairs tested:
		- BZ=F vs CL=F   (Brent vs WTI crude)
		- GOOGL vs META  (tech equities)
		- SPY vs QQQ     (index ETFs)
		- V vs MA        (payment processors)
	"""
	# Define pairs
	pairs = [
		("BZ=F", "CL=F"),
		("GOOGL", "META"),
		("SPY", "QQQ"),
		("V", "MA")
	]

	# Create /data folder if missing
	Path("data").mkdir(exist_ok=True)

	# Define parameter grid for optimisation
	config = GridSearchConfig(
		lookbacks=[20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100, 120],
		entry_zs=[1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0],
		exit_zs=[0.1, 0.25, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0],
		min_trades=10,
		min_obs=200
	)

	print("=" * 70)
	print("PARAMETER OPTIMISATION - GRID SEARCH")
	print("=" * 70)
	total_combos = len(list(config.lookbacks)) * len(list(config.entry_zs)) * len(list(config.exit_zs))
	
	print(f"\nParameter Space:")
	print(f"  Lookbacks:  {len(list(config.lookbacks))} values from {min(config.lookbacks)} to {max(config.lookbacks)}")
	print(f"  Entry Z:    {len(list(config.entry_zs))} values from {min(config.entry_zs):.2f} to {max(config.entry_zs):.2f}")
	print(f"  Exit Z:     {len(list(config.exit_zs))} values from {min(config.exit_zs):.2f} to {max(config.exit_zs):.2f}")
	print(f"  Min Trades: {config.min_trades}")
	print(f"  Min Obs:    {config.min_obs}")
	print(f"\nTotal combinations per pair: {total_combos:,}")
	print("=" * 70)

	# Store results for cross-pair comparison
	all_results = {}

	# Loop through each pair
	for ticker_a, ticker_b in pairs:
		print(f"\n{'=' * 70}")
		print(f"Optimising parameters for {ticker_a} vs {ticker_b}")
		print(f"{'=' * 70}\n")

		# Download data
		print(f"Downloading data for {ticker_a} and {ticker_b}...")
		df = download_data(ticker_a, ticker_b)
		if df.empty:
			print(f"No data returned for {ticker_a} and {ticker_b}. Skipping.\n")
			continue

		print(f"Downloaded {len(df)} rows of data.\n")

		# Run grid search
		results = grid_search(df, config, show_progress=True)

		if results.empty:
			print(f"\nNo valid configurations found for {ticker_a} vs {ticker_b}.\n")
			continue

		# Save full results to CSV
		pair_name = f"{ticker_a.replace('=', '')}_{ticker_b.replace('=', '')}"
		results_path = Path("data") / f"{pair_name}_optimisation.csv"
		results.to_csv(results_path, index=False)
		print(f"\nSaved full results to {results_path.resolve()}")

		# Store for comparison
		all_results[pair_name] = results

		# Display top 5 configurations
		print(f"\n{'─' * 70}")
		print(f"TOP 5 CONFIGURATIONS FOR {ticker_a} vs {ticker_b}")
		print(f"{'─' * 70}")

		top_5 = results.head(5)
		for rank, row in enumerate(top_5.itertuples(index=False), start=1):
			print(f"\nRank {rank}")
			print(f"  Lookback window : {int(row.lookback)} days")
			print(f"  Entry threshold  : {row.entry_z}")
			print(f"  Exit threshold   : {row.exit_z}")
			print(f"  Sharpe ratio     : {round(row.sharpe_ratio, 2)}")
			print(f"  Total return     : {round(row.total_return, 4)}")
			print(f"  Max drawdown     : {round(row.max_drawdown, 4)}")
			print(f"  Win rate         : {round(row.win_rate * 100, 1)}%")
			print(f"  Trades executed  : {int(row.num_trades)}")
			print(f"  Profit factor    : {round(row.profit_factor, 2)}")

		# Show best config summary
		best = results.iloc[0]
		print(f"\n{'─' * 70}")
		print("OPTIMAL CONFIGURATION")
		print(f"  Lookback window : {int(best['lookback'])} days")
		print(f"  Entry threshold : {best['entry_z']}")
		print(f"  Exit threshold  : {best['exit_z']}")
		print(f"  Sharpe ratio    : {round(best['sharpe_ratio'], 2)}")
		print(f"  Total return    : {round(best['total_return'], 4)}")
		print(f"  Win rate        : {round(best['win_rate'] * 100, 1)}%")
		print(f"  Profit factor   : {round(best['profit_factor'], 2)}")
		print(f"{'─' * 70}")

		# Generate heatmap visualisation if enabled
		if show_graphs and len(results) > 0:
			_plot_parameter_heatmap(results, ticker_a, ticker_b)

	# Cross-pair comparison summary
	if all_results:
		print(f"\n{'=' * 70}")
		print("CROSS-PAIR COMPARISON - BEST CONFIGURATIONS")
		print(f"{'=' * 70}\n")

		for pair_name, results in all_results.items():
			best = results.iloc[0]
			print(f"{pair_name:20s} | LB={int(best['lookback']):2d} | Entry={best['entry_z']:.2f} | Exit={best['exit_z']:.2f} | Sharpe={best['sharpe_ratio']:>6.2f} | Return={best['total_return']:>7.4f}")

		print(f"\n{'=' * 70}")

	print("\nAll optimisations complete.")


def _plot_parameter_heatmap(results, ticker_a, ticker_b):
	"""
	Generate heatmap visualisation of Sharpe ratio across parameter space.

	Args:
		results : pd.DataFrame
			Grid search results containing parameters and metrics.
		ticker_a : str
			First ticker symbol.
		ticker_b : str
			Second ticker symbol.
	"""
	# Create figure with subplots for different lookback windows
	unique_lookbacks = sorted(results['lookback'].unique())
	n_lookbacks = len(unique_lookbacks)
	
	fig, axes = plt.subplots(1, n_lookbacks, figsize=(5 * n_lookbacks, 4))
	if n_lookbacks == 1:
		axes = [axes]
	
	fig.suptitle(f"{ticker_a} vs {ticker_b} - Sharpe Ratio Heatmap", fontsize=14, fontweight='bold')

	for idx, lookback in enumerate(unique_lookbacks):
		ax = axes[idx]
		
		# Filter results for this lookback
		subset = results[results['lookback'] == lookback]
		
		# Create pivot table for heatmap
		pivot = subset.pivot_table(
			values='sharpe_ratio',
			index='entry_z',
			columns='exit_z',
			aggfunc='mean'
		)
		
		# Plot heatmap
		im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', origin='lower')
		
		# Set ticks and labels
		ax.set_xticks(range(len(pivot.columns)))
		ax.set_yticks(range(len(pivot.index)))
		ax.set_xticklabels([f"{x:.2f}" for x in pivot.columns])
		ax.set_yticklabels([f"{y:.2f}" for y in pivot.index])
		
		# Labels
		ax.set_xlabel('Exit Z-Score', fontsize=10)
		ax.set_ylabel('Entry Z-Score', fontsize=10)
		ax.set_title(f'Lookback = {int(lookback)}', fontsize=11)
		
		# Add colorbar
		cbar = plt.colorbar(im, ax=ax)
		cbar.set_label('Sharpe Ratio', rotation=270, labelpad=15)
		
		# Annotate cells with values
		for i in range(len(pivot.index)):
			for j in range(len(pivot.columns)):
				value = pivot.values[i, j]
				if not np.isnan(value):
					text_color = 'white' if value < pivot.values.mean() else 'black'
					ax.text(j, i, f'{value:.2f}', ha='center', va='center', 
						   color=text_color, fontsize=8, fontweight='bold')

	plt.tight_layout()
	plt.show()


if __name__ == "__main__":
	SHOW_GRAPHS = False
	main(show_graphs=SHOW_GRAPHS)
