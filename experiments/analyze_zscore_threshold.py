# experiments/analyze_zscore_threshold.py

## Imports
import sys
from pathlib import Path
import pandas as pd
import glob

# Allow imports from /src when running this script directly
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))


## Functions
def analyse_zscore_distributions():
    """
    Analyse z-score distributions across all processed CSV files.
    
    This script helps determine appropriate z-score thresholds for
    pairs trading signals by examining:
    - Min/Max z-score values
    - Mean and standard deviation
    - Percentage of observations exceeding various thresholds
    
    Thresholds analysed: ±1.0, ±1.5, ±2.0, ±2.5, ±3.0
    """
    files = glob.glob('data/*_processed.csv')
    
    if not files:
        print("No processed CSV files found in data/ directory.")
        return
    
    print('Z-Score Distribution Analysis')
    print('='*70)
    
    for file in files:
        filename = Path(file).name
        print(f'\n{filename}:')
        
        df = pd.read_csv(file)
        z = df['zscore']
        
        print(f'  Min: {z.min():.2f}, Max: {z.max():.2f}')
        print(f'  Mean: {z.mean():.3f}, Std: {z.std():.2f}')
        print(f'  |z| > 1.0: {(z.abs() > 1.0).sum() / len(z) * 100:.1f}%')
        print(f'  |z| > 1.5: {(z.abs() > 1.5).sum() / len(z) * 100:.1f}%')
        print(f'  |z| > 2.0: {(z.abs() > 2.0).sum() / len(z) * 100:.1f}%')
        print(f'  |z| > 2.5: {(z.abs() > 2.5).sum() / len(z) * 100:.1f}%')
        print(f'  |z| > 3.0: {(z.abs() > 3.0).sum() / len(z) * 100:.1f}%')


def main():
    """Main entry point for the script."""
    analyse_zscore_distributions()


if __name__ == "__main__":
    main()
