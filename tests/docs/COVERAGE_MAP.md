# Test Coverage Map - LASE

| Source Module | Function / Class | Test Function(s) | Coverage Notes |
|----------------|------------------|------------------|----------------|
| src/data_utils.py | download_data | test_valid_tickers_returns_dataframe | Verifies correct data structure |
| src/data_utils.py | download_data | test_invalid_ticker_returns_empty_dataframe | Checks robustness to bad inputs |
| src/data_utils.py | download_data | test_index_is_timezone_aware | Validates timezone consistency |
| src/data_utils.py | download_data | test_default_date_range_is_recent | Confirms sensible defaults |
| src/data_utils.py | download_data | test_same_tickers_returns_single_series_data | Ensures same-ticker inputs are handled safely and logically |
