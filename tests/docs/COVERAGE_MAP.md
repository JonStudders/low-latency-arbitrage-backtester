# Test Coverage Map - LASE

| Source Module | Function / Class | Test Function(s) | Coverage Notes |
|----------------|------------------|------------------|----------------|
| src/data_utils.py | download_data | test_valid_tickers_returns_dataframe | Verifies correct data structure |
| src/data_utils.py | download_data | test_invalid_ticker_returns_empty_dataframe | Checks robustness to bad inputs |
| src/data_utils.py | download_data | test_index_is_timezone_aware | Validates timezone consistency |
| src/data_utils.py | download_data | test_default_date_range_is_recent | Confirms sensible defaults |
| src/data_utils.py | download_data | test_same_tickers_returns_single_series_data | Ensures same-ticker inputs are handled safely and logically |
| src/data_utils.py | _safe_download | test_safe_download_invalid_ticker_returns_empty | Confirms that invalid tickers return an empty Series instead of raising errors |
| src/preprocess.py | prepare_spread | test_prepare_spread_returns_expected_columns | Verifies output columns and structure |
| src/preprocess.py | prepare_spread | test_prepare_spread_computes_valid_zscores | Checks rolling z-score correctness |
| src/preprocess.py | prepare_spread | test_prepare_spread_raises_for_invalid_columns | Confirms defensive input validation |
| src/preprocess.py | prepare_spread | test_prepare_spread_handles_missing_data_gracefully | Ensures NaN cleaning post-rolling |
| src/preprocess.py | prepare_spread | test_prepare_spread_respects_lookback_window | Validates proper rolling window truncation |