# Jon Studders - LASE: Low-Latency Arbitrage Strategy Engine

A high-performance statistical arbitrage system designed for pair-trading highly correlated assets, including equities, index products, and commodity futures. The engine uses Python for backtesting and statistical modelling, with plans to optimise the critical Z-score signal generation kernel in C++ using pybind11 for production deployment.

## Why LASE?

**LASE** stands for **Low-Latency Arbitrage Strategy Engine** — a name that encapsulates the system’s three foundational principles:

| Term | Meaning | Relevance |
|------|----------|-----------|
| **Low-Latency** | Focuses on high-performance, C++-based computation and efficient data handling. | Demonstrates proficiency in real-time analytics and performance engineering — key capabilities in quantitative systems development. |
| **Arbitrage** | Implements statistical arbitrage by exploiting temporary pricing deviations between correlated assets. | Reflects applied understanding of quantitative finance, correlation structures, and mean-reversion modelling. |
| **Strategy** | Extends beyond data processing to incorporate complete trading logic, from signal generation to backtesting. | Emphasises end-to-end system design and evaluation within a research-to-production workflow. |
| **Engine** | Designed as a modular, extensible architecture capable of supporting multiple asset classes and execution layers. | Positions the project as a scalable and maintainable platform rather than a single-purpose prototype. |

## Inspiration

This project was inspired by [Max Margenot's excellent talk on pairs trading](https://www.youtube.com/watch?v=g-qvFjvyqcs), which provided valuable insights into statistical arbitrage strategies and their practical implementation. Special thanks to [Max Margenot](https://www.linkedin.com/in/mmargenot/) for sharing his expertise with the quantitative finance community.

Also thanks to [Statistical Arbitrage for the Uninitiated (no fluff)](https://www.youtube.com/watch?v=-Fr-Nz-uO2U). 

## Project Goals

This project was developed to demonstrate expertise in statistical arbitrage across diverse rival asset classes, including:
- **Equities**: Visa (V) vs. Mastercard (MA), and Alphabet (GOOGL) vs. Meta Platforms (META).
- **Indices**: S&P 500 ETF (SPY) vs. Nasdaq 100 ETF (QQQ).
- **Commodities**: WTI Crude Oil Futures (CL=F) vs. Brent Crude Oil Futures (BZ=F).

The technical focus remains on three key areas:
1. **Statistical Modelling**: Implementing a mean-reversion strategy based on the relationship between two correlated financial assets.
2. **Financial Domain Knowledge**: Applying the strategy to pair trading across different markets and calculating standard backtesting metrics (Sharpe Ratio, Max Drawdown).
3. **Low-Latency Optimisation**: Current Python implementation with planned C++ acceleration for rolling Z-score calculations to meet sub-millisecond latency requirements in production (Phase 4).

## Tech Stack

### Python (Current Implementation)
- `NumPy`, `pandas`, `statsmodels`, `matplotlib`, `yfinance`, `tqdm`
- Data ingestion, cointegration testing, backtesting, visualisation

### C++ (Planned - Phase 4)
- `pybind11` for Python bindings

## Features

- **Robust Data Download**: Automated market data retrieval from Yahoo Finance with timezone-aware date handling
- **Spread Analysis**: Computes price spreads between asset pairs with configurable rolling windows
- **Z-Score Calculation**: Statistical normalisation for mean-reversion signal generation
- **Error Handling**: Graceful handling of invalid tickers, missing data, and API failures
- **Comprehensive Testing**: Full test coverage with pytest for data utilities and preprocessing functions
- **Experimentation Tools**: Scripts for batch processing and visualisation of multiple asset pairs

## Installation

### Prerequisites
- Python 3.11+
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd LASE
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Project Structure

```
LASE/
├── data/                           # Market data files (CSV format)
│   ├── *_backtest.csv             # Backtest results with PnL and metrics
│   ├── *_signals.csv              # Generated trading signals
│   ├── *_processed.csv            # Preprocessed spread and z-score data
│   └── *.csv                      # Raw downloaded price data
├── experiments/                    # Experimental scripts and validation tools
│   ├── analyze_zscore_threshold.py # Z-score distribution analysis
│   ├── run_backtest_test.py       # Full pipeline backtest with metrics
│   ├── run_data_utils_test.py     # Data download validation
│   ├── run_preprocess_test.py     # Spread preprocessing validation
│   └── run_signals_test.py        # Signal generation validation
├── src/                            # Source code modules
│   ├── __init__.py                # Package initialisation
│   ├── backtest.py                # Backtesting engine (PnL calculation)
│   ├── data_utils.py              # Market data download and utilities
│   ├── metrics.py                 # Performance metrics (Sharpe, Sortino, drawdown, etc.)
│   ├── preprocess.py              # Spread calculation and z-score preprocessing
│   └── signals.py                 # Trading signal generation logic
├── tests/                          # Test suite (53 tests, 100% coverage)
│   ├── test_backtest.py           # Tests for backtest engine (14 tests)
│   ├── test_data_utils.py         # Tests for data download functions (5 tests)
│   ├── test_metrics.py            # Tests for performance metrics (16 tests)
│   ├── test_preprocess.py         # Tests for spread preprocessing (11 tests)
│   ├── test_signals.py            # Tests for signal generation (7 tests)
│   └── docs/                      # Test documentation
│       ├── COVERAGE_MAP.md        # Test-to-function coverage mapping
│       └── TEST_PLAN.md           # Detailed test specifications
├── PROCESS.md                      # End-to-end workflow documentation
├── ROADMAP.md                      # Phased development plan
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
└── README.md                       # This file
```

## Usage

### Basic Usage

#### Downloading Market Data

```python
from src.data_utils import download_data
from datetime import datetime
import pytz

# Download data with default 5-year window
df = download_data("SPY", "QQQ")

# Download data with custom date range
start = datetime(2020, 1, 1, tzinfo=pytz.UTC)
end = datetime.now(pytz.UTC)
df = download_data("V", "MA", start=start, end=end)
```

#### Preparing Spread Data

```python
from src.preprocess import prepare_spread

# Calculate spread and z-scores with default 60-day lookback
processed_df = prepare_spread(df, lookback=60)

# Access computed columns
spread = processed_df["spread"]
zscore = processed_df["zscore"]
spread_mean = processed_df["spread_mean"]
spread_std = processed_df["spread_std"]
```

### Running Experiments

#### Download Data for Multiple Pairs

```bash
python experiments/run_data_utils_test.py
```

This script downloads market data for four asset pairs:
- BZ=F vs CL=F (Brent vs WTI crude)
- GOOGL vs META (tech equities)
- SPY vs QQQ (index ETFs)
- V vs MA (payment processors)

#### Process and Visualise Spreads

```bash
python experiments/run_preprocess_test.py
```

This script:
- Downloads data for multiple asset pairs
- Computes spreads and z-scores
- Generates visualisation plots
- Saves processed data to CSV files

## Testing

Run the full test suite:

```bash
pytest
```

Run tests for a specific module:

```bash
pytest tests/test_data_utils.py
pytest tests/test_preprocess.py
```

View test coverage (requires `pytest-cov`):

```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

### Test Coverage

The project maintains comprehensive test coverage for:
- Data download functionality with various ticker inputs
- Error handling for invalid tickers and missing data
- Timezone standardisation
- Spread calculation accuracy
- Z-score computation validation
- Rolling window behaviour

See `tests/docs/TEST_PLAN.md` and `tests/docs/COVERAGE_MAP.md` for detailed testing documentation.

## Data Files

The `data/` directory contains both raw and processed market data:
- **Raw data** (`*.csv`): Historical price data downloaded from Yahoo Finance
- **Processed data** (`*_processed.csv`): Data enriched with spread, rolling statistics, and z-scores

## Future Enhancements 
### Adaptive Preprocessing

#### Dynamic Hedge Ratio Estimation (Kalman Filter)
- Replace the fixed rolling-OLS hedge ratio with a Kalman filter to estimate a time-varying βₜ.
- This improves responsiveness to changing market regimes while reducing noise and lag in the spread definition.

#### Adaptive Lookback Calibration

Instead of a fixed 60-day window, calibrate the z-score lookback (N) using the mean-reversion half-life of each pair:

- N = 2-4 * (t)

This makes the z-score normalisation pair-specific and statistically justified.

## Notes

- This project uses Yahoo Finance API through the `yfinance` library
- The system has no automatic retry mechanism for failed API calls
- All timestamps are standardised to UTC for consistency
- Missing data points are dropped during alignment (no forward/backward fill)
- Initially 'Raw Spread' was used in the data processing, but I opt'd for Hedge Ratio due to the Scalability and industry standard.

## License

MIT License

Copyright (c) 2024 Jon Studders

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Author

**Jon Studders**
- LinkedIn: [Jon Studders](https://www.linkedin.com/in/jon-studders-1236841a4/)
- GitHub: [@JonStudders](https://github.com/JonStudders/LASE)
