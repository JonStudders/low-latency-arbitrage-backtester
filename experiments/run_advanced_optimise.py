# experiments/run_advanced_optimise.py
# Advanced parameter optimisation experiments with walk-forward validation,
# robustness analysis, transaction cost sensitivity, and stable region identification.

## Imports
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data_utils import download_data
from optimise import (
	GridSearchConfig, grid_search, walk_forward_validation,
	robustness_analysis, transaction_cost_analysis, identify_stable_regions
)


## Main
def main():
	"""Run advanced optimisation analysis on a single pair."""
	
	# Select pair for detailed analysis
	ticker_a, ticker_b = "SPY", "QQQ"
	
	print("=" * 70)
	print("ADVANCED PARAMETER OPTIMISATION ANALYSIS")
	print("=" * 70)
	print(f"\nAnalysing {ticker_a} vs {ticker_b}\n")
	
	# Download data
	print(f"Downloading data for {ticker_a} and {ticker_b}...")
	df = download_data(ticker_a, ticker_b)
	if df.empty:
		print(f"No data returned. Exiting.")
		return
	
	print(f"Downloaded {len(df)} rows of data.\n")
	
	# Define parameter grid
	config = GridSearchConfig(
		lookbacks=[20, 30, 40, 50, 60, 70, 80, 90, 100],
		entry_zs=[1.5, 2.0, 2.5, 3.0],
		exit_zs=[0.25, 0.5, 0.75, 1.0],
		min_trades=10,
		min_obs=200
	)
	
	# 1. Walk-Forward Validation
	print("\n" + "=" * 70)
	print("1. WALK-FORWARD VALIDATION (70/30 TRAIN/TEST SPLIT)")
	print("=" * 70 + "\n")
	
	wf_result = walk_forward_validation(df, config, train_fraction=0.7, show_progress=True)
	
	if wf_result['train_sharpe'] and wf_result['test_sharpe']:
		print(f"\n{'─' * 70}")
		print("WALK-FORWARD SUMMARY")
		print(f"{'─' * 70}")
		print(f"Training Sharpe:     {round(wf_result['train_sharpe'], 2)}")
		print(f"Test Sharpe:         {round(wf_result['test_sharpe'], 2)}")
		print(f"Sharpe Degradation:  {round(wf_result['sharpe_degradation'], 1)}%")
		
		if wf_result['sharpe_degradation'] < 20:
			print("✓ Low degradation - parameters generalise well")
		elif wf_result['sharpe_degradation'] < 40:
			print("⚠ Moderate degradation - some overfitting present")
		else:
			print("✗ High degradation - significant overfitting detected")
	
	# 2. Robustness Analysis
	print("\n" + "=" * 70)
	print("2. ROBUSTNESS ANALYSIS (3 TIME PERIODS)")
	print("=" * 70 + "\n")
	
	robust_results = robustness_analysis(df, config, n_periods=3, show_progress=False)
	
	if not robust_results.empty:
		print(f"\n{'─' * 70}")
		print("PERIOD-BY-PERIOD RESULTS")
		print(f"{'─' * 70}")
		print(robust_results[['period', 'lookback', 'entry_z', 'exit_z', 'sharpe_ratio', 'num_trades']].to_string(index=False))
	
	# 3. Transaction Cost Analysis
	print("\n" + "=" * 70)
	print("3. TRANSACTION COST SENSITIVITY ANALYSIS")
	print("=" * 70 + "\n")
	
	cost_results = transaction_cost_analysis(
		df, config,
		cost_bps_range=[0, 5, 10, 20, 50],
		show_progress=False
	)
	
	if not cost_results.empty:
		print(f"\n{'─' * 70}")
		print("COST IMPACT ON OPTIMAL PARAMETERS")
		print(f"{'─' * 70}")
		print(cost_results.to_string(index=False))
		
		# Analyse how parameters change with costs
		if len(cost_results) > 1:
			entry_z_change = cost_results.iloc[-1]['entry_z'] - cost_results.iloc[0]['entry_z']
			trades_change = cost_results.iloc[-1]['num_trades'] - cost_results.iloc[0]['num_trades']
			
			print(f"\n{'─' * 70}")
			print("COST SENSITIVITY INSIGHTS")
			print(f"{'─' * 70}")
			print(f"Entry Z change (0→50 bps):  {round(entry_z_change, 2)}")
			print(f"Trade count change:          {trades_change:+g}")
			
			if entry_z_change > 0.5:
				print("Success: Strategy adapts well to costs (wider thresholds)")
			else:
				print("Warning: Strategy may be cost-sensitive")
	
	# 4. Stable Region Identification
	print("\n" + "=" * 70)
	print("4. STABLE PARAMETER REGION IDENTIFICATION")
	print("=" * 70 + "\n")
	
	# Get full grid search results
	print("Running full grid search for stability analysis...")
	all_results = grid_search(df, config, show_progress=False)
	
	if not all_results.empty:
		stability = identify_stable_regions(all_results, top_n=10)
		
		print(f"\n{'─' * 70}")
		print("STABILITY ANALYSIS (TOP 10 CONFIGURATIONS)")
		print(f"{'─' * 70}")
		print(f"Lookback range:      {stability['lookback_range'][0]} - {stability['lookback_range'][1]} days")
		print(f"Entry Z range:       {round(stability['entry_z_range'][0], 2)} - {round(stability['entry_z_range'][1], 2)}")
		print(f"Exit Z range:        {round(stability['exit_z_range'][0], 2)} - {round(stability['exit_z_range'][1], 2)}")
		print(f"\nLookback stable:     {'True' if stability['lookback_stable'] else 'False'}")
		print(f"Entry Z stable:      {'True' if stability['entry_z_stable'] else 'False'}")
		print(f"Exit Z stable:       {'True' if stability['exit_z_stable'] else 'False'}")
		print(f"Overall stable:      {'True' if stability['overall_stable'] else 'False'}")
		
		print(f"\n{'─' * 70}")
		print("RECOMMENDED PARAMETERS (MEDIAN OF TOP 10)")
		print(f"{'─' * 70}")
		print(f"Lookback:  {stability['median_params']['lookback']} days")
		print(f"Entry Z:   {round(stability['median_params']['entry_z'], 2)}")
		print(f"Exit Z:    {round(stability['median_params']['exit_z'], 2)}")
		
		if stability['overall_stable']:
			print("\nSuccess: Parameters are robust - low sensitivity to small changes")
		else:
			print("\nWarning: Parameters show variation - consider broader testing")
	
	# 5. Final Recommendations
	print("\n" + "=" * 70)
	print("5. FINAL RECOMMENDATIONS")
	print("=" * 70 + "\n")
	
	if all([
		wf_result.get('sharpe_degradation', 100) < 30,
		stability.get('overall_stable', False),
		cost_results.iloc[0]['sharpe_ratio'] > 0.5 if not cost_results.empty else False
	]):
		print("Success: Strategy shows strong characteristics:")
		print("  - Low overfitting (walk-forward validation)")
		print("  - Stable parameter regions")
		print("  - Positive risk-adjusted returns")
		print("\n-> Recommended for live trading consideration")
	else:
		print("Warning: Strategy requires further refinement:")
		if wf_result.get('sharpe_degradation', 100) >= 30:
			print("  - High walk-forward degradation detected")
		if not stability.get('overall_stable', False):
			print("  - Parameter instability across top configurations")
		if cost_results.empty or cost_results.iloc[0]['sharpe_ratio'] <= 0.5:
			print("  - Weak risk-adjusted performance")
		print("\n-> Consider expanding parameter space or testing different pairs")
	
	print("\n" + "=" * 70)
	print("Analysis complete.")
	print("=" * 70)


if __name__ == "__main__":
	main()
