# Test Plan - LASE Data Layer

## Module: src/data_utils.py
Component under test: `download_data()`

### Purpose
Ensure that market data download and preparation works correctly, handles errors gracefully,
and produces standardized, timezone-aware datasets for later analytics.

---

### Tests and Their Intent

| Test Name | Behavior Verified | Rationale |
|------------|-------------------|------------|
| `test_valid_tickers_returns_dataframe` | Returns non-empty DataFrame with correct columns for valid tickers | Core functionality: must fetch and align data correctly |
| `test_invalid_ticker_returns_empty_dataframe` | Returns empty DataFrame for invalid or delisted tickers | Ensures graceful failure instead of crashing |
| `test_index_is_timezone_aware` | Output index has UTC timezone | Guarantees consistent time alignment across datasets |
| `test_default_date_range_is_recent` | Uses dynamic UTC window (~5 years) when no dates are provided | Confirms default behavior is practical and reproducible |
| `test_same_tickers_returns_single_series_data` | Handles identical ticker inputs correctly (no crash or duplication) | Prevents logical errors when user accidentally provides same ticker twice |
| `test_safe_download_invalid_ticker_returns_empty` | Ensures that `_safe_download()` returns an empty Series when provided with an invalid or unavailable ticker symbol | Verifies robustness and fault tolerance at the lowest data-fetching level, ensuring consistent behavior even when API calls fail |

---

## Module: src/preprocess.py
Component under test: `prepare_spread()`

### Purpose
To validate the **spread preparation and statistical normalization** process used to generate mean-reversion trading signals.

---

### Tests and Their Intent

| Test Name | Behavior Verified | Rationale |
|------------|-------------------|------------|
| `test_prepare_spread_returns_expected_columns` | Ensures the returned DataFrame contains spread analysis columns (`spread`, `spread_mean`, `spread_std`, `zscore`) | Confirms structural integrity of preprocessing output |
| `test_prepare_spread_computes_valid_zscores` | Validates correct numerical computation of z-scores over the rolling window | Confirms statistical accuracy of spread normalization |
| `test_prepare_spread_raises_for_invalid_columns` | Raises a ValueError if input DataFrame has more or fewer than two columns | Ensures defensive error handling for malformed data |
| `test_prepare_spread_handles_missing_data_gracefully` | Ensures missing data are handled cleanly and NaNs are dropped after rolling ops | Confirms data hygiene before signal generation |
| `test_prepare_spread_respects_lookback_window` | Verifies the output length matches expected rolling-window truncation | Confirms correct rolling window behavior |

---

### Notes
- All tests are written in `pytest` and follow AAA (Arrange–Act–Assert) structure.
- Data sources are mocked or conditionally short-circuited to reduce API calls when possible.
- Each test focuses on a single responsibility, avoiding overlap.