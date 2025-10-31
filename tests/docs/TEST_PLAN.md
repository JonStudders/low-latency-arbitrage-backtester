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
| `test_qqq_returns_empty_dataframe` | Returns empty DataFrame when 'QQQ' used | Simulates empty dataset for downstream edge-case testing |
| `test_invalid_ticker_returns_empty_dataframe` | Returns empty DataFrame for invalid or delisted tickers | Ensures graceful failure instead of crashing |
| `test_index_is_timezone_aware` | Output index has UTC timezone | Guarantees consistent time alignment across datasets |
| `test_default_date_range_is_recent` | Uses dynamic UTC window (~5 years) when no dates are provided | Confirms default behavior is practical and reproducible |

---

### Notes
- All tests are written in `pytest` and follow AAA (Arrange–Act–Assert) structure.
- Data sources are mocked or conditionally short-circuited to reduce API calls when possible.
- Each test focuses on a single responsibility, avoiding overlap.