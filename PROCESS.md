# Process Reference
This document explains the end-to-end workflow of the pairs trading pipeline in plain English.  
It provides a step-by-step outline of how data is downloaded, processed, and transformed into standardised trading signals.

---

## Process 1 — Data Download
Implemented in: `/src/data_utils.py`

We download historical price data for two assets using **Yahoo Finance** (`yfinance`).  
The goal is to collect clean, time-aligned data that can be compared directly between both assets.

**Steps performed:**
1. Download both asset price series over a consistent time window.  
2. Align timestamps so that every date has valid prices for both assets.  
3. Handle missing data by removing dates where one asset has no price, or filling in small gaps where needed to prevent misalignment.  
4. Convert all timestamps to **UTC** to ensure both datasets share the same timezone reference.

**The output:**

A clean DataFrame with:
- **Two price columns**: One for each asset (e.g., `SPY`, `QQQ`)
- **UTC-indexed dates**: All timestamps standardised to UTC timezone
- **No missing values**: Rows with incomplete data removed
- **Aligned dates**: Only dates where both assets have valid prices

This process ensures the dataset is synchronised and reliable before we start comparing the prices.

---

## Process 2 — Spread Calculation
Implemented in: `/src/preprocess.py`

Once both price series are aligned, we measure how far they move relative to one another.

**The problem:** Two assets might have very different prices. For example, one might cost £100 per share while the other costs £50 per share. We need to account for this difference so we can compare their movements fairly.

### Hedge Ratio (β)
The hedge ratio adjusts for differences in scale between the two assets.  
Think of it as a conversion factor that tells us how much Asset A typically moves when Asset B moves by a certain amount.

For example, if the hedge ratio is 2.0, it means Asset A usually moves twice as much as Asset B.  
This helps us create a fair comparison by accounting for the fact that one asset might be more volatile or expensive than the other.

The hedge ratio is calculated by looking at how the two assets have moved together over the last 60 days:

\[
β_t = \frac{\text{Cov}(A_t, B_t)}{\text{Var}(B_t)}
\]

This represents how much Asset A typically moves for every 1-unit move in Asset B over the last *N* observations (default = 60).  
It normalises the relationship so we can compare relative movements rather than raw prices.

### Spread
The spread quantifies how far apart the two normalised prices are:

\[
Spread_t = A_t - β_t \times B_t
\]

- If the spread widens, one asset has become expensive relative to the other.  
- If the spread narrows, the pair is converging back toward equilibrium.

The spread captures relative mispricing and forms the foundation of the pairs trading strategy.

**The output:**

The function adds four new columns to our data:
- **`beta`**: The rolling hedge ratio (β) between the two assets
- **`spread`**: The adjusted price difference (A - β × B)
- **`spread_mean`**: Rolling average of the spread over the lookback window
- **`spread_std`**: Rolling standard deviation of the spread

These columns prepare the data for z-score calculation in the next step.

---

## Process 3 — Z-Score Normalisation
Implemented in: `/src/preprocess.py`

We standardise the spread into a **z-score** to measure how unusual the current spread is compared to its recent history.

\[
Z_t = \frac{Spread_t - \text{Mean}(Spread_{t-N:t})}{\text{Std}(Spread_{t-N:t})}
\]

- \(Z_t = 0\): the pair is balanced (normal relationship)  
- \(Z_t > +2\): the spread is unusually wide (potential short signal)  
- \(Z_t < -2\): the spread is unusually narrow (potential long signal)

**The output:**

The function adds one critical column:
- **`zscore`**: The standardised spread value

This z-score is the primary signal we monitor. Values near zero indicate normal behaviour, while extreme values (beyond ±2) suggest trading opportunities.

The z-score converts spreads into a consistent statistical scale, allowing all asset pairs to be compared on equal terms.

---

## Process 4 — Calculating Optimal Z-Score Threshold
Implemented in: `/experiments/analyze_zscore_threshold.py`

We need to decide how far apart the prices must be before we place a trade.  
If we trade too early, we might lose money on false signals. If we wait too long, we miss good opportunities.

**What we do:**
1. Run the analysis script on all our processed data files.  
2. The script looks at each pair's historical z-score data.  
3. It counts how often the z-score goes above different levels (like 1.0, 1.5, 2.0, 2.5, or 3.0).  
4. We review the results and pick a threshold that gives us enough trading chances without being too risky.

**Example output from the script:**

```
BZF_CLF_processed.csv:
  Min: -3.70, Max: 4.25
  Mean: 0.136, Std: 1.44
  |z| > 1.0: 55.7%
  |z| > 1.5: 33.0%
  |z| > 2.0: 15.8%
  |z| > 2.5: 6.0%
  |z| > 3.0: 2.5%
```

The numbers show, for example, that 15.8% of the time the z-score was more than 2.0 points away from zero.  
This tells us how often we would get trading signals at each threshold level.

**We chose ±2.0 as our threshold.**

This gives us enough trading opportunities (about 15-20% of days) without generating too many false signals.

This means we only trade when the z-score is more than 2 points away from zero.  
Across all pairs, this happens about 15-20 times per 100 days, which gives us enough opportunities without overtrading.

---

## Process 5 — Generating Trading Signals
Implemented in: `/src/signals.py`

At this stage, we have z-scores that tell us how unusual the price relationship is.  
Now we need to convert these numbers into actual trading decisions: when to open a trade, when to close it, and what direction to trade.

**The basic idea:**

When the z-score shows that prices are very far apart (above +2 or below -2), we open a trade.  
When the z-score returns to normal levels (within ±0.5), we close the trade.

**How it works:**

1. **Opening a trade:**
   - If the z-score goes above +2, it means the first asset is too expensive compared to the second.  
     We open a **short** trade: we sell the first asset and buy the second, betting that prices will come back together.
   - If the z-score goes below -2, it means the first asset is too cheap compared to the second.  
     We open a **long** trade: we buy the first asset and sell the second, betting that prices will converge.

2. **Keeping the trade open:**
   - Once we've opened a trade, we keep it open until the z-score returns to normal.  
     This prevents us from opening and closing trades too frequently, which would increase costs and reduce profits.

3. **Closing the trade:**
   - When the z-score returns to within ±0.5 (close to zero), we close the trade.  
     At this point, the prices have returned to their normal relationship, so we take our profit and wait for the next opportunity.

**The output:**

The function adds a new column called "signal" to our data:
- **+1** means we have a long position open (buy first, sell second)
- **-1** means we have a short position open (sell first, buy second)
- **0** means we have no position (we're waiting for the next opportunity)

This signal column tells us exactly what trade to make on each day, based on how far apart the prices have moved.

---

## Process 6 — Backtesting
Implemented in: `/src/backtest.py`

At this stage, we have trading signals that tell us when to open and close positions.  
Now we need to simulate how those trades would have performed historically to measure profitability and risk.

**The goal:**

Calculate the profit and loss (PnL) that would have been generated if we had followed our trading signals in the past.  
This helps us understand whether the strategy is profitable and how much risk we're taking.

**How it works:**

1. **Calculate spread returns:**
   - For each day, we measure how much the spread changed compared to the previous day.
   - This is calculated as: `spread_return = (spread_today - spread_yesterday) / spread_yesterday`
   - The spread return tells us how much the price relationship moved, which directly affects our profit or loss.

2. **Apply signals to returns:**
   - We multiply the spread return by the signal from the **previous day**.
   - This is critical: we use the previous day's signal because we can only trade based on information available before today.
   - If we had a **long position** (+1) and the spread increased, we make money.
   - If we had a **short position** (-1) and the spread decreased, we make money.
   - If we had **no position** (0), we make no profit or loss.

3. **Prevent look-ahead bias:**
   - The signal is shifted by one period to ensure we're not using today's information to make today's trade.
   - This simulates realistic trading conditions where we can only act on yesterday's closing signal.
   - The first row always has zero PnL because there's no prior signal to trade on.

4. **Calculate cumulative PnL:**
   - We sum up all the daily profits and losses to track total performance over time.
   - This shows us how the strategy would have grown (or declined) our capital over the entire period.

**The output:**

The backtest adds three new columns to our data:
- **`spread_ret`**: The percentage change in the spread from one day to the next
- **`pnl`**: The profit or loss for each day based on our position
- **`cum_pnl`**: The cumulative total of all profits and losses up to that point

**Example:**

If the spread was 10 yesterday and 11 today, and we had a long position:
- Spread return = (11 - 10) / 10 = 0.10 (10% increase)
- PnL = 0.10 × 1 (long signal) = +0.10 (we made 10%)

If we had a short position instead:
- PnL = 0.10 × -1 (short signal) = -0.10 (we lost 10%)

This process transforms our trading signals into measurable financial outcomes, allowing us to evaluate whether the strategy is worth implementing with real capital.

---

## Process 7 — Performance Metrics
Implemented in: `/src/metrics.py`

After running the backtest, we need to evaluate how good the strategy actually is.  
Raw profit numbers don't tell the full story, we need to understand the risk we took to achieve those returns.

**The goal:**

Calculate industry-standard performance metrics that allow us to compare this strategy against other investment opportunities and assess whether the returns justify the risks.

**What we calculate:**

1. **Total Return**  
   The final cumulative profit or loss over the entire backtest period.  
   This is simply the last value in our cumulative PnL column.

2. **Sharpe Ratio**  
   Measures risk-adjusted returns by comparing average profit to total volatility.  
   Formula: (Average Daily Return / Standard Deviation of Returns) × √252  
   
   - A Sharpe ratio above 1.0 is considered acceptable  
   - Above 2.0 is very good  
   - Above 3.0 is excellent  
   
   The √252 factor annualises the ratio (252 trading days per year).

3. **Sortino Ratio**  
   Similar to Sharpe ratio but only penalises downside volatility (negative returns).  
   Formula: (Average Daily Return / Downside Standard Deviation) × √252  
   
   - More relevant for strategies with asymmetric return distributions  
   - Higher Sortino ratio indicates better risk-adjusted returns  
   - Typically higher than Sharpe ratio since it ignores upside volatility

3. **Maximum Drawdown**  
   The worst peak-to-trough decline in cumulative PnL.  
   This tells us the largest loss we would have experienced from any previous high point.  
   
   For example, if our strategy grew from £0 to £1000, then dropped to £700, the maximum drawdown is -£300.  
   This metric is critical for understanding downside risk.

4. **Win Rate**  
   The percentage of days where we made money (only counting days with active positions).  
   A 60% win rate means we were profitable on 6 out of every 10 trading days.

5. **Number of Trades**  
   Total count of position changes throughout the backtest.  
   This helps us understand trading frequency and potential transaction costs.

6. **Turnover**  
   Average daily absolute position change.  
   Measures how frequently positions are adjusted.  
   
   - Higher turnover indicates more active trading  
   - Important for estimating transaction costs  
   - Calculated as mean of absolute signal changes

7. **Average Win / Average Loss**  
   The mean profit on winning days and mean loss on losing days.  
   These metrics help us understand the risk-reward profile of individual trades.

8. **Profit Factor**  
   Ratio of gross profits to gross losses.  
   
   - Profit factor > 1.0 means the strategy is profitable overall  
   - Profit factor of 2.0 means we make £2 for every £1 we lose  
   - Values below 1.0 indicate a losing strategy

**The output:**

A dictionary containing all ten metrics, which can be printed as a performance summary or saved for comparison across different asset pairs or strategy configurations.

**Example output:**

```
Performance Metrics:
  Total Return:     0.1250  (12.5% cumulative return)
  Sharpe Ratio:     1.85    (good risk-adjusted performance)
  Sortino Ratio:    2.12    (better downside risk-adjusted performance)
  Max Drawdown:    -0.0450  (-4.5% worst decline)
  Win Rate:         0.58    (58% of trades profitable)
  Num Trades:       42      (42 position changes)
  Turnover:         0.0325  (average daily position change)
  Avg Win:          0.0025  (0.25% average profit per winning day)
  Avg Loss:        -0.0018  (-0.18% average loss per losing day)
  Profit Factor:    1.65    (£1.65 profit per £1 loss)
```

These metrics allow us to answer critical questions:
- Is the strategy profitable after accounting for risk?
- How much capital drawdown should we expect?
- Does the strategy generate enough trades to be practical?
- Are the wins large enough to compensate for the losses?

---

## Process 8 — Parameter Optimisation
Implemented in: `/src/optimise.py`

After building a working strategy, we need to find the best settings to maximise performance.  
Think of this like tuning a radio to get the clearest signal—we're adjusting three key dials to find the optimal combination.

**The problem:**

Our strategy has three important settings that affect how it behaves:
1. **Lookback window**: How many days of history to use when calculating the spread's average (30, 60, or 90 days?)
2. **Entry threshold**: How far apart must prices be before we open a trade? (z-score of 1.5, 2.0, or 2.5?)
3. **Exit threshold**: How close must prices return before we close the trade? (z-score of 0.25, 0.5, or 0.75?)

Different settings work better for different asset pairs. Some pairs need wider thresholds to avoid false signals, while others need tighter thresholds to capture quick movements.

**What we do:**

We test every possible combination of these settings systematically—this is called a **grid search**.

For example, if we test:
- 3 lookback windows (30, 60, 90 days)
- 3 entry thresholds (1.5, 2.0, 2.5)
- 3 exit thresholds (0.25, 0.5, 0.75)

That gives us 3 × 3 × 3 = 27 different combinations to evaluate.

**How it works:**

1. **Generate all combinations**: Create a list of every possible parameter set.

2. **Run backtest for each combination**: For each set of parameters:
   - Calculate the spread using that lookback window
   - Generate trading signals using those entry/exit thresholds
   - Run a backtest to measure performance
   - Calculate all performance metrics (Sharpe ratio, returns, drawdown, etc.)

3. **Apply quality filters**: Remove unreliable configurations that:
   - Don't generate enough trades (fewer than 10)
   - Don't have enough data after the warmup period (fewer than 200 observations)
   - Have invalid settings (entry threshold smaller than exit threshold)

4. **Rank by performance**: Sort all valid configurations by Sharpe ratio (risk-adjusted returns).  
   The configuration with the highest Sharpe ratio becomes our optimal parameter set.

5. **Analyse stability**: Look at the top 5-10 configurations to see if they use similar parameters.  
   If the best settings are all clustered together (e.g., lookback between 45-75 days), that suggests the strategy is robust.  
   If the top results are scattered randomly, the strategy might be unreliable.

**The output:**

The optimisation produces:
- **Full results table**: Every configuration tested, sorted by performance
- **Best configuration**: The single parameter set with highest Sharpe ratio
- **Derived metrics**: Additional insights like return-per-trade and drawdown-to-return ratio
- **Visualisations** (optional): Heatmaps showing how Sharpe ratio changes across the parameter space

**Example output:**

```
Testing 45 parameter combinations...
Found 38 valid configurations.

TOP 5 CONFIGURATIONS FOR SPY vs QQQ:

Rank 1:
  Parameters:    lookback=60, entry_z=2.00, exit_z=0.50
  Sharpe Ratio:      2.15
  Total Return:      0.1250
  Max Drawdown:     -0.0350
  Win Rate:          58.5%
  Num Trades:        42
  Profit Factor:     1.85

Rank 2:
  Parameters:    lookback=75, entry_z=2.00, exit_z=0.50
  Sharpe Ratio:      2.08
  Total Return:      0.1180
  ...
```

**Why this matters:**

Without optimisation, we'd be guessing at the best parameters. We might choose settings that work poorly, missing profitable opportunities or taking unnecessary risks.

By systematically testing all combinations, we:
- **Maximise risk-adjusted returns**: Find the settings that give the best Sharpe ratio
- **Understand robustness**: See if small parameter changes dramatically affect performance
- **Avoid overfitting**: Use quality filters to ensure we have enough trades for statistical validity
- **Compare across pairs**: Identify whether different asset pairs need different settings

**Important considerations:**

1. **Overfitting risk**: Just because a parameter set performed best historically doesn't guarantee future success.  
   We look for stable regions where multiple nearby parameter sets perform well, not just a single "magic" combination.

2. **Transaction costs**: More trades mean higher costs. A configuration with Sharpe ratio of 2.0 and 100 trades might be worse than Sharpe 1.9 with 30 trades once we account for fees.

3. **Walk-forward validation**: Test parameters on one time period, then validate on a different period to ensure they generalise.

This optimisation process transforms our strategy from a fixed set of rules into an adaptive system that can be tuned for different market conditions and asset pairs.

---

## Process 9 — Walk-Forward Validation
Implemented in: `/src/optimise.py` (walk_forward_validation function)

After finding optimal parameters, we need to test if they actually work on new, unseen data—or if we've just found patterns that only existed in our training period.

**The problem:**

When we optimise parameters on historical data, there's a risk of **overfitting**: finding parameters that work perfectly on that specific time period but fail miserably on new data. It's like memorising exam answers instead of understanding the subject—you'll ace that specific test but fail when the questions change.

**What we do:**

We split our data into two parts:
1. **Training period** (typically 70% of data): Used to find optimal parameters
2. **Testing period** (remaining 30%): Used to validate if those parameters still work

This is called **walk-forward validation** because we "walk forward" in time from training to testing.

**How it works:**

1. **Split the data**: If we have 1,000 days of data, use the first 700 days for training and the last 300 for testing.

2. **Optimise on training data**: Run grid search on the 700-day training period to find the best parameters.

3. **Test on unseen data**: Apply those exact same parameters to the 300-day testing period and measure performance.

4. **Compare results**: Calculate how much performance degrades from training to testing.

**Example:**

```
Training period: 700 days
  Best parameters found: lookback=60, entry_z=2.0, exit_z=0.5
  Training Sharpe ratio: 2.15

Testing period: 300 days (using same parameters)
  Testing Sharpe ratio: 1.95
  Degradation: 9.3%
```

**Interpreting results:**

- **Low degradation (0-20%)**: Parameters generalise well. The strategy is robust.
- **Moderate degradation (20-40%)**: Some overfitting present. Parameters work but with reduced performance.
- **High degradation (40%+)**: Significant overfitting. Parameters don't generalise—back to the drawing board.
- **Negative test Sharpe**: Complete failure. Parameters are useless on new data.

**Why this matters:**

Without walk-forward validation, you might deploy a strategy that looked amazing in backtests but loses money in live trading. This process helps separate genuinely robust strategies from lucky curve-fitting.

---

## Process 10 — Robustness Analysis
Implemented in: `/src/optimise.py` (robustness_analysis function)

Even if parameters pass walk-forward validation, we want to know if they work consistently across different market conditions—or if they only work in specific regimes.

**The problem:**

Markets change. What works during a bull market might fail during a bear market. What works when volatility is low might break when volatility spikes. We need to test if our parameters are **robust** across different conditions.

**What we do:**

We split the data into multiple consecutive periods (typically 3-4) and find the optimal parameters for each period separately. If the optimal parameters are similar across all periods, the strategy is robust. If they're wildly different, the strategy is regime-dependent.

**How it works:**

1. **Split into periods**: Divide 1,000 days into 3 periods of ~333 days each.

2. **Optimise each period**: Run grid search on each period independently.

3. **Compare results**: Look at the optimal parameters from each period.

**Example:**

```
Period 1 (Days 1-333):
  Best: lookback=60, entry_z=2.0, exit_z=0.5
  Sharpe: 2.10

Period 2 (Days 334-666):
  Best: lookback=65, entry_z=2.0, exit_z=0.5
  Sharpe: 1.95

Period 3 (Days 667-1000):
  Best: lookback=55, entry_z=2.25, exit_z=0.5
  Sharpe: 2.05

Summary:
  Lookback range: 55-65 (stable)
  Entry Z range: 2.0-2.25 (stable)
  Exit Z range: 0.5 (very stable)
  Mean Sharpe: 2.03
```

**Interpreting results:**

- **Consistent parameters**: If lookback varies by ±10 days and thresholds by ±0.25, the strategy is robust.
- **Variable parameters**: If lookback swings from 30 to 120 or thresholds from 1.0 to 3.0, the strategy is regime-dependent.
- **Consistent Sharpe**: If Sharpe ratio stays positive across all periods, the strategy has persistent edge.

**Why this matters:**

A robust strategy works across bull markets, bear markets, high volatility, and low volatility. A regime-dependent strategy might work brilliantly for 6 months then fail catastrophically when conditions change.

---

## Process 11 — Transaction Cost Sensitivity
Implemented in: `/src/optimise.py` (transaction_cost_analysis function)

Real trading isn't free. Every trade incurs costs: exchange fees, bid-ask spread, slippage, and potentially market impact. We need to know how these costs affect our strategy.

**The problem:**

A strategy that generates 100 trades might look profitable in a zero-cost backtest but become unprofitable once you account for 10 basis points (0.1%) per trade. We need to understand the **break-even cost** and how parameters should change as costs increase.

**What we do:**

We test the same strategy at different cost levels (0, 5, 10, 20, 50 basis points) and see:
1. How profitability degrades with costs
2. Whether optimal parameters change (they should favour fewer trades as costs increase)
3. What the break-even cost is

**How it works:**

1. **Run baseline optimisation**: Find optimal parameters assuming zero costs.

2. **Apply costs**: For each cost level, calculate:
   - Cost per trade = 2 × cost_bps / 10,000 (multiply by 2 for entry + exit)
   - Total cost drag = num_trades × cost_per_trade
   - Return after costs = total_return - cost_drag

3. **Re-rank configurations**: Sort by Sharpe ratio after costs.

4. **Compare optimal parameters**: See if the best configuration changes.

**Example:**

```
0 bps cost:
  Best: lookback=60, entry_z=2.0, exit_z=0.5
  Trades: 100, Sharpe: 2.15

10 bps cost:
  Best: lookback=60, entry_z=2.25, exit_z=0.5
  Trades: 75, Sharpe: 1.85

20 bps cost:
  Best: lookback=75, entry_z=2.5, exit_z=0.75
  Trades: 50, Sharpe: 1.45

50 bps cost:
  Best: lookback=90, entry_z=3.0, exit_z=1.0
  Trades: 25, Sharpe: 0.65
```

**Interpreting results:**

- **Entry thresholds increase**: Higher costs favour wider entry thresholds (fewer trades).
- **Exit thresholds increase**: Wider exits reduce round-trip frequency.
- **Sharpe degrades**: Performance decreases as costs increase.
- **Break-even cost**: The cost level where Sharpe drops to zero.

**Why this matters:**

If your strategy becomes unprofitable at 15 bps but your broker charges 20 bps, you'll lose money. This analysis helps you:
- Negotiate better execution costs
- Adjust parameters for your actual cost structure
- Decide if the strategy is viable given your constraints

---

## Process 12 — Stable Parameter Region Identification
Implemented in: `/src/optimise.py` (identify_stable_regions function)

The final validation step: checking if the top-performing configurations cluster together or are scattered randomly across the parameter space.

**The problem:**

If the #1 configuration has lookback=60 but #2 has lookback=120, and #3 has lookback=30, the strategy is **unstable**—small changes in parameters cause huge performance swings. This suggests overfitting.

If the top 10 configurations all have lookback between 55-65, entry_z between 1.75-2.25, and exit_z between 0.4-0.6, the strategy is **stable**—there's a robust region of good parameters.

**What we do:**

We examine the top N configurations (typically 10) and check if their parameters cluster together within a tolerance range.

**How it works:**

1. **Take top 10 configurations**: Get the 10 best parameter sets by Sharpe ratio.

2. **Calculate ranges**:
   - Lookback range: min to max lookback values
   - Entry Z range: min to max entry thresholds
   - Exit Z range: min to max exit thresholds

3. **Check tolerance**:
   - Lookback stable if range ≤ 15 days
   - Entry Z stable if range ≤ 0.5
   - Exit Z stable if range ≤ 0.25

4. **Calculate median**: Use median parameters from the stable region as final recommendation.

**Example:**

```
Top 10 configurations:
  Lookback: 55, 60, 60, 60, 65, 60, 65, 55, 60, 65
  Entry Z: 2.0, 2.0, 2.25, 2.0, 2.0, 2.25, 2.0, 2.25, 2.0, 2.25
  Exit Z: 0.5, 0.5, 0.5, 0.5, 0.5, 0.75, 0.5, 0.5, 0.5, 0.5

Analysis:
  Lookback range: 55-65 (10 days) ✓ STABLE
  Entry Z range: 2.0-2.25 (0.25) ✓ STABLE
  Exit Z range: 0.5-0.75 (0.25) ✓ STABLE
  Overall: STABLE

Recommended parameters (median):
  Lookback: 60 days
  Entry Z: 2.0
  Exit Z: 0.5
```

**Interpreting results:**

- **All stable**: High confidence in parameters. Small variations won't hurt performance.
- **Some unstable**: Moderate confidence. Be careful with the unstable parameters.
- **All unstable**: Low confidence. The strategy might be curve-fitted to noise.

**Why this matters:**

In live trading, you can't execute with the exact parameters from your backtest. Market conditions shift slightly, your execution timing differs, and real-world constraints apply. If your strategy only works with one precise parameter set, it will fail in production. Stable regions give you confidence that the strategy will work even with minor parameter variations.

---

## Summary: Complete Optimisation Workflow

The full optimisation process combines all these steps:

1. **Grid Search**: Find candidate parameter sets
2. **Walk-Forward Validation**: Test if parameters generalise to new data
3. **Robustness Analysis**: Test if parameters work across different market regimes
4. **Transaction Cost Sensitivity**: Adjust for real-world trading costs
5. **Stable Region Identification**: Confirm parameters aren't overfitted

Only strategies that pass all five tests should be considered for live trading. This rigorous validation process separates genuinely profitable strategies from statistical flukes.
