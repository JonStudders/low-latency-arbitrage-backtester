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
| `test_beta_calculation_accuracy` | Verifies hedge ratio (beta) is calculated correctly for known asset relationships | Validates core mathematical correctness of beta estimation |
| `test_spread_calculation_with_known_beta` | Confirms spread = A - beta * B formula is implemented correctly | Ensures spread calculation matches theoretical definition |
| `test_zscore_has_zero_mean_unit_variance` | Validates z-score normalisation produces approximately zero mean (rolling z-scores have time-varying variance, not unit variance) | Confirms statistical properties of rolling z-score transformation |
| `test_constant_spread_produces_zero_zscore` | Ensures truly constant prices produce zero z-scores when std=0 | Handles edge case of zero variance gracefully without NaN errors |
| `test_beta_backfill_handles_initial_nans` | Verifies beta is backfilled for initial rows where rolling window is incomplete | Ensures no NaN values in beta column after processing |
| `test_spread_column_exists_and_is_numeric` | Confirms spread column is created with numeric dtype and no missing values | Basic structural validation of spread output |

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

## Module: src/backtest.py
Component under test: `run_backtest()`

### Purpose
To validate the **backtesting engine** that simulates historical trading performance.
Verify correct PnL calculation, look-ahead bias prevention, and economic logic of long/short positions.

---

### Tests and Their Intent

| Test Name | Behaviour Verified | Rationale |
|------------|------------------|------------|
| `test_run_backtest_returns_expected_columns` | Returns DataFrame with required columns (`spread_ret`, `pnl`, `cum_pnl`) | Confirms structural integrity of backtest output |
| `test_run_backtest_computes_valid_pnl` | Cumulative PnL equals sum of incremental PnL | Validates mathematical consistency of PnL accumulation |
| `test_run_backtest_raises_for_missing_columns` | Raises ValueError when required input columns are missing | Ensures defensive validation of input data |
| `test_flat_signal_results_in_zero_pnl` | Flat (zero) signals produce no profit or loss | Confirms no PnL is generated without active positions |
| `test_signal_shift_prevents_lookahead_bias` | Signals are shifted to prevent look-ahead bias | Critical validation that prevents unrealistic backtest results |
| `test_long_position_profits_from_spread_increase` | Long positions (+1) make money when spread increases | Validates core economic logic of long positions |
| `test_short_position_profits_from_spread_decrease` | Short positions (-1) make money when spread decreases | Validates core economic logic of short positions |
| `test_long_position_loses_from_spread_decrease` | Long positions lose money when spread decreases | Confirms correct sign of losses for long positions |
| `test_position_flip_from_long_to_short` | PnL calculated correctly during position transitions | Ensures signal lag is handled properly during flips |
| `test_position_entry_from_flat` | PnL is zero during entry period (using prior flat signal) | Validates signal shift during position entry |
| `test_spread_return_calculation` | Spread returns calculated as percentage change | Confirms correct return calculation methodology |
| `test_pnl_calculation_with_known_values` | Hand-calculated PnL values match implementation | Validates numerical precision with known test cases |
| `test_empty_dataframe_handling` | Empty DataFrame handled gracefully | Edge case validation for empty inputs |
| `test_single_row_dataframe` | Single row produces zero PnL (no prior signal) | Edge case validation for minimal input |

---

## Module: src/backtest.py
Component under test: `calculate_performance_metrics()`

### Purpose
To validate the **performance metrics calculation** that evaluates trading strategy quality.
Verify correct computation of risk-adjusted returns, drawdown analysis, and trade statistics.

---

### Tests and Their Intent

| Test Name | Behaviour Verified | Rationale |
|------------|------------------|------------|
| `test_calculate_performance_metrics_returns_expected_keys` | Returns dictionary with all required metric keys | Confirms structural integrity of metrics output |
| `test_calculate_performance_metrics_raises_for_missing_columns` | Raises ValueError when required input columns are missing | Ensures defensive validation of input data |
| `test_total_return_calculation` | Total return equals final cumulative PnL value | Validates basic return calculation |
| `test_sharpe_ratio_calculation` | Sharpe ratio computed correctly with annualisation factor | Confirms risk-adjusted return calculation |
| `test_max_drawdown_calculation` | Maximum drawdown captures worst peak-to-trough decline | Validates downside risk measurement |
| `test_win_rate_calculation` | Win rate percentage calculated correctly from profitable days | Confirms trade success rate calculation |
| `test_num_trades_calculation` | Number of trades counts position changes accurately | Validates trade frequency tracking |
| `test_avg_win_and_avg_loss_calculation` | Average win and loss values computed correctly | Confirms risk-reward profile calculation |
| `test_profit_factor_calculation` | Profit factor ratio calculated as gross profit / gross loss | Validates profitability ratio |
| `test_empty_dataframe_returns_default_metrics` | Empty DataFrame handled gracefully with default values | Edge case validation for empty inputs |
| `test_all_winning_trades_profit_factor` | Profit factor is infinity when there are no losses | Handles edge case of perfect strategy |
| `test_all_losing_trades_profit_factor` | Profit factor is NaN when there are no wins | Handles edge case of losing strategy |
| `test_win_rate_with_no_active_positions` | Win rate is zero when no positions are taken | Validates behaviour with flat signals only |

---

### Notes
- All tests are written in `pytest` and follow AAA (Arrange–Act–Assert) structure.
- Data sources are mocked or conditionally short-circuited to reduce API calls when possible.
- Each test focuses on a single responsibility, avoiding overlap.
- `yfinance.download()` is now mocked in all data layer tests to remove live API dependencies and ensure deterministic, offline test execution.
- Backtest tests emphasise **economic correctness** (PnL signs) and **look-ahead bias prevention**, which are critical for valid strategy evaluation.