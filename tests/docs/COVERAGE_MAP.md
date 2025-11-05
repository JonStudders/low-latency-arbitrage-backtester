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
| src/signals.py | generate_trade_signals | test_valid_dataframe_generates_signals | Verifies correct output structure with signal column |
| src/signals.py | generate_trade_signals | test_entry_and_exit_behavior | Confirms entry and exit logic based on z-score thresholds |
| src/signals.py | generate_trade_signals | test_forward_fill_maintains_position | Ensures position persistence until exit condition |
| src/signals.py | generate_trade_signals | test_negative_zscore_creates_long_signal | Validates symmetric handling of negative z-scores |
| src/signals.py | generate_trade_signals | test_threshold_validation | Checks that entry_z must be greater than exit_z |
| src/signals.py | generate_trade_signals | test_missing_column_raises_error | Confirms defensive validation for missing zscore column |
| src/signals.py | generate_trade_signals | test_nan_values_do_not_break_signal_generation | Ensures NaN values don't break signal continuity |