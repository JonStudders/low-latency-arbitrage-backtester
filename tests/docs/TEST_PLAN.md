# Test Plan - LASE Data Layer

## Module: src/data_utils.py
Component under test: `download_data()`

### Purpose
Ensure that market data download and preparation works correctly, handles errors gracefully,
and produces standardised, timezone-aware datasets for later analytics.

---

### Tests and Their Intent

| Test Name | Behaviour Verified | Rationale |
|------------|-------------------|------------|
| `test_valid_tickers_returns_dataframe` | Returns non-empty DataFrame with correct columns for valid tickers | Core functionality: must fetch and align data correctly |
| `test_invalid_ticker_returns_empty_dataframe` | Returns empty DataFrame for invalid or delisted tickers | Ensures graceful failure instead of crashing |
| `test_index_is_timezone_aware` | Output index has UTC timezone | Guarantees consistent time alignment across datasets |
| `test_default_date_range_is_recent` | Uses dynamic UTC window (~5 years) when no dates are provided | Confirms default behaviour is practical and reproducible |
| `test_same_tickers_returns_single_series_data` | Handles identical ticker inputs correctly (no crash or duplication) | Prevents logical errors when user accidentally provides same ticker twice |
| `test_safe_download_invalid_ticker_returns_empty` | Ensures that `_safe_download()` returns an empty Series when provided with an invalid or unavailable ticker symbol | Verifies robustness and fault tolerance at the lowest data-fetching level, ensuring consistent behaviour even when API calls fail |

---

## Module: src/preprocess.py
Component under test: `prepare_spread()`

### Purpose
To validate the **spread preparation and statistical normalisation** process used to generate mean-reversion trading signals.

---

### Tests and Their Intent

| Test Name | Behaviour Verified | Rationale |
|------------|-------------------|------------|
| `test_prepare_spread_returns_expected_columns` | Ensures the returned DataFrame contains spread analysis columns (`spread`, `spread_mean`, `spread_std`, `zscore`) | Confirms structural integrity of preprocessing output |
| `test_prepare_spread_computes_valid_zscores` | Validates correct numerical computation of z-scores over the rolling window | Confirms statistical accuracy of spread normalisation |
| `test_prepare_spread_raises_for_invalid_columns` | Raises a ValueError if input DataFrame has more or fewer than two columns | Ensures defensive error handling for malformed data |
| `test_prepare_spread_handles_missing_data_gracefully` | Ensures missing data are handled cleanly and NaNs are dropped after rolling ops | Confirms data hygiene before signal generation |
| `test_prepare_spread_respects_lookback_window` | Verifies the output length matches expected rolling-window truncation | Confirms correct rolling window behaviour |

---

## Module: src/signals.py
Component under test: `generate_trade_signals()`

### Purpose
Translate the spread’s z-score into deterministic long, short, or flat trading signals based on mean reversion logic.
Verify correct entry, exit, and persistence behaviour under all common scenarios.

---

### Tests and Their Intent

| Test Name | Behaviour Verified | Rationale |
|------------|------------------|------------|
| `test_valid_dataframe_generates_signals` | Function outputs valid DataFrame with signal column | Confirms base functionality |
| `test_entry_and_exit_behavior` | Correctly opens and closes trades around ±entry_z / ±exit_z thresholds | Core rule validation |
| `test_forward_fill_maintains_position` | Keeps prior position active until z-score returns within exit band | Ensures position persistence |
| `test_negative_zscore_creates_long_signal` | Handles negative side (long spread) symmetrically | Confirms sign consistency |
| `test_threshold_validation` | entry_z must be greater than exit_z | Prevents unstable config |
| `test_missing_column_raises_error` | Raises when required column is missing | Defensive validation |
| `test_nan_values_do_not_break_signal_generation` | Ignores NaNs but maintains correct signal continuity | Robust to missing data |

---

### Notes
- All tests are written in `pytest` and follow AAA (Arrange–Act–Assert) structure.
- Data sources are mocked or conditionally short-circuited to reduce API calls when possible.
- Each test focuses on a single responsibility, avoiding overlap.
- `yfinance.download()` is now mocked in all data layer tests to remove live API dependencies and ensure deterministic, offline test execution.