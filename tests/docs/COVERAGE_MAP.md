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
| src/preprocess.py | prepare_spread | test_beta_calculation_accuracy | Validates hedge ratio calculation with known asset relationships |
| src/preprocess.py | prepare_spread | test_spread_calculation_with_known_beta | Confirms spread formula implementation correctness |
| src/preprocess.py | prepare_spread | test_zscore_has_zero_mean_unit_variance | Validates rolling z-scores have approximately zero mean (not unit variance due to time-varying local normalisation) |
| src/preprocess.py | prepare_spread | test_constant_spread_produces_zero_zscore | Ensures constant prices produce zero z-scores without NaN errors when std=0 |
| src/preprocess.py | prepare_spread | test_beta_backfill_handles_initial_nans | Confirms beta backfill eliminates NaN values |
| src/preprocess.py | prepare_spread | test_spread_column_exists_and_is_numeric | Validates spread column creation and data type |
| src/signals.py | generate_trade_signals | test_valid_dataframe_generates_signals | Verifies correct output structure with signal column |
| src/signals.py | generate_trade_signals | test_entry_and_exit_behavior | Confirms entry and exit logic based on z-score thresholds |
| src/signals.py | generate_trade_signals | test_forward_fill_maintains_position | Ensures position persistence until exit condition |
| src/signals.py | generate_trade_signals | test_negative_zscore_creates_long_signal | Validates symmetric handling of negative z-scores |
| src/signals.py | generate_trade_signals | test_threshold_validation | Checks that entry_z must be greater than exit_z |
| src/signals.py | generate_trade_signals | test_missing_column_raises_error | Confirms defensive validation for missing zscore column |
| src/signals.py | generate_trade_signals | test_nan_values_do_not_break_signal_generation | Ensures NaN values don't break signal continuity |
| src/backtest.py | run_backtest | test_run_backtest_returns_expected_columns | Verifies output contains spread_ret, pnl, and cum_pnl columns |
| src/backtest.py | run_backtest | test_run_backtest_computes_valid_pnl | Validates cumulative PnL equals sum of incremental PnL |
| src/backtest.py | run_backtest | test_run_backtest_raises_for_missing_columns | Ensures ValueError raised for missing required columns |
| src/backtest.py | run_backtest | test_flat_signal_results_in_zero_pnl | Confirms zero PnL when no positions are held |
| src/backtest.py | run_backtest | test_signal_shift_prevents_lookahead_bias | Critical validation preventing look-ahead bias |
| src/backtest.py | run_backtest | test_long_position_profits_from_spread_increase | Validates long position economic logic (profit on rise) |
| src/backtest.py | run_backtest | test_short_position_profits_from_spread_decrease | Validates short position economic logic (profit on fall) |
| src/backtest.py | run_backtest | test_long_position_loses_from_spread_decrease | Confirms long positions lose when spread falls |
| src/backtest.py | run_backtest | test_position_flip_from_long_to_short | Validates PnL calculation during position transitions |
| src/backtest.py | run_backtest | test_position_entry_from_flat | Confirms zero PnL during entry period due to signal lag |
| src/backtest.py | run_backtest | test_spread_return_calculation | Validates spread return calculated as percentage change |
| src/backtest.py | run_backtest | test_pnl_calculation_with_known_values | Confirms numerical precision with hand-calculated values |
| src/backtest.py | run_backtest | test_empty_dataframe_handling | Edge case validation for empty inputs |
| src/backtest.py | run_backtest | test_single_row_dataframe | Edge case validation for single-row inputs |
| src/metrics.py | calculate_performance_metrics | test_calculate_performance_metrics_returns_expected_keys | Verifies output dictionary contains all 10 required metric keys (including Sortino and turnover) |
| src/metrics.py | calculate_performance_metrics | test_calculate_performance_metrics_raises_for_missing_columns | Ensures ValueError raised when required columns (pnl, cum_pnl, signal) are missing |
| src/metrics.py | calculate_performance_metrics | test_total_return_calculation | Validates total return equals final cumulative PnL value |
| src/metrics.py | calculate_performance_metrics | test_sharpe_ratio_calculation | Confirms Sharpe ratio computed with correct annualisation factor (√252) |
| src/metrics.py | calculate_performance_metrics | test_sortino_ratio_calculation | Validates Sortino ratio uses only downside volatility for risk-adjusted returns |
| src/metrics.py | calculate_performance_metrics | test_max_drawdown_calculation | Validates maximum drawdown captures worst peak-to-trough decline |
| src/metrics.py | calculate_performance_metrics | test_win_rate_calculation | Confirms win rate calculated as percentage of profitable days with active positions |
| src/metrics.py | calculate_performance_metrics | test_num_trades_calculation | Validates trade count equals number of position changes (signal transitions) |
| src/metrics.py | calculate_performance_metrics | test_turnover_calculation | Confirms turnover measures average daily absolute position change |
| src/metrics.py | calculate_performance_metrics | test_avg_win_and_avg_loss_calculation | Confirms average win and average loss calculated correctly from winning/losing days |
| src/metrics.py | calculate_performance_metrics | test_profit_factor_calculation | Validates profit factor as ratio of gross profits to gross losses |
| src/metrics.py | calculate_performance_metrics | test_empty_dataframe_returns_default_metrics | Edge case: empty DataFrame returns sensible default values without crashing |
| src/metrics.py | calculate_performance_metrics | test_all_winning_trades_profit_factor | Edge case: profit factor is infinity when there are no losses |
| src/metrics.py | calculate_performance_metrics | test_all_losing_trades_profit_factor | Edge case: profit factor is 0.0 when there are no wins |
| src/metrics.py | calculate_performance_metrics | test_win_rate_with_no_active_positions | Edge case: win rate is 0.0 when all signals are flat (no positions taken) |
| src/metrics.py | calculate_performance_metrics | test_sortino_ratio_with_no_downside | Edge case: Sortino ratio is NaN when there are no negative returns (no downside volatility) |