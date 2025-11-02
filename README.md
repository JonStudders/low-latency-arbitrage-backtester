# Jon Studders - low-latency-arbitrage-backtester

A high-performance statistical arbitrage system designed for pair-trading highly correlated assets, including equities, index products, and commodity futures. The engine uses Python for backtesting and statistical modelling, with the critical, low-latency Z-score signal generation kernel implemented and optimised in C++ using pybind11.

## Project Goals

This project was developed to demonstrate expertise in statistical arbitrage across diverse rival asset classes, including:
- **Equities**: Visa (V) vs. Mastercard (MA), and Alphabet (GOOGL) vs. Meta Platforms (META).
- **Indices**: S&P 500 ETF (SPY) vs. Nasdaq 100 ETF (QQQ).
- **Commodities**: WTI Crude Oil Futures (CL=F) vs. Brent Crude Oil Futures (BZ=F).

The technical focus remains on three key areas:
1. **Statistical Modelling**: Implementing a mean-reversion strategy based on the relationship between two correlated financial assets.
2. **Financial Domain Knowledge**: Applying the strategy to pair trading across different markets and calculating standard backtesting metrics (Sharpe Ratio, Max Drawdown).
3. **Low-Latency Optimisation**: Offloading the high-frequency calculation of the rolling Z-score to a dedicated C++ kernel to simulate real-time performance requirements.

## Tech Stack

### Python
- `NumPy`, `pandas`, `statsmodels`, `matplotlib`, `yfinance`, `tqdm`
- Data ingestion, cointegration testing, backtesting, visualization

### C++:
- Lib 1
- Lib 2

## Features

- **Robust Data Download**: Automated market data retrieval from Yahoo Finance with timezone-aware date handling
- **Spread Analysis**: Computes price spreads between asset pairs with configurable rolling windows
- **Z-Score Calculation**: Statistical normalization for mean-reversion signal generation
- **Error Handling**: Graceful handling of invalid tickers, missing data, and API failures
- **Comprehensive Testing**: Full test coverage with pytest for data utilities and preprocessing functions
- **Experimentation Tools**: Scripts for batch processing and visualization of multiple asset pairs

## Installation

### Prerequisites
- Python 3.11+
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd low-latency-arbitrage-backtester
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
low-latency-arbitrage-backtester/
├── data/                    # Market data files (CSV format)
│   ├── *_processed.csv     # Preprocessed spread and z-score data
│   └── *.csv               # Raw downloaded price data
├── experiments/            # Experimental scripts and validation tools
│   ├── run_data_utils_test.py
│   └── run_preprocess_test.py
├── src/                    # Source code modules
│   ├── data_utils.py       # Market data download and utilities
│   └── preprocess.py       # Spread calculation and z-score preprocessing
├── tests/                  # Test suite
│   ├── test_data_utils.py  # Tests for data download functions
│   ├── test_preprocess.py  # Tests for spread preprocessing
│   └── docs/               # Test documentation
│       ├── TEST_PLAN.md
│       └── COVERAGE_MAP.md
├── requirements.txt        # Python dependencies
├── pytest.ini             # Pytest configuration
└── README.md              # This file
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

#### Process and Visualize Spreads

```bash
python experiments/run_preprocess_test.py
```

This script:
- Downloads data for multiple asset pairs
- Computes spreads and z-scores
- Generates visualization plots
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
- Timezone standardization
- Spread calculation accuracy
- Z-score computation validation
- Rolling window behavior

See `tests/docs/TEST_PLAN.md` and `tests/docs/COVERAGE_MAP.md` for detailed testing documentation.

## Data Files

The `data/` directory contains both raw and processed market data:
- **Raw data** (`*.csv`): Historical price data downloaded from Yahoo Finance
- **Processed data** (`*_processed.csv`): Data enriched with spread, rolling statistics, and z-scores

## Notes

- This project uses Yahoo Finance API through the `yfinance` library
- The system has no automatic retry mechanism for failed API calls
- All timestamps are standardized to UTC for consistency
- Missing data points are dropped during alignment (no forward/backward fill)

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
