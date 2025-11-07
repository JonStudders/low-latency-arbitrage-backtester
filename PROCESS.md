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
Implemented in: `/src/backtest.py`

After running the backtest, we need to evaluate how good the strategy actually is.  
Raw profit numbers don't tell the full story, we need to understand the risk we took to achieve those returns.

**The goal:**

Calculate industry-standard performance metrics that allow us to compare this strategy against other investment opportunities and assess whether the returns justify the risks.

**What we calculate:**

1. **Total Return**  
   The final cumulative profit or loss over the entire backtest period.  
   This is simply the last value in our cumulative PnL column.

2. **Sharpe Ratio**  
   Measures risk-adjusted returns by comparing average profit to volatility.  
   Formula: (Average Daily Return / Standard Deviation of Returns) × √252  
   
   - A Sharpe ratio above 1.0 is considered acceptable  
   - Above 2.0 is very good  
   - Above 3.0 is excellent  
   
   The √252 factor annualises the ratio (252 trading days per year).

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

6. **Average Win / Average Loss**  
   The mean profit on winning days and mean loss on losing days.  
   These metrics help us understand the risk-reward profile of individual trades.

7. **Profit Factor**  
   Ratio of gross profits to gross losses.  
   
   - Profit factor > 1.0 means the strategy is profitable overall  
   - Profit factor of 2.0 means we make £2 for every £1 we lose  
   - Values below 1.0 indicate a losing strategy

**The output:**

A dictionary containing all eight metrics, which can be printed as a performance summary or saved for comparison across different asset pairs or strategy configurations.

**Example output:**

```
Performance Metrics:
  Total Return:     0.1250  (12.5% cumulative return)
  Sharpe Ratio:     1.85    (good risk-adjusted performance)
  Max Drawdown:    -0.0450  (-4.5% worst decline)
  Win Rate:         0.58    (58% of trades profitable)
  Num Trades:       42      (42 position changes)
  Avg Win:          0.0025  (0.25% average profit per winning day)
  Avg Loss:        -0.0018  (-0.18% average loss per losing day)
  Profit Factor:    1.65    (£1.65 profit per £1 loss)
```

These metrics allow us to answer critical questions:
- Is the strategy profitable after accounting for risk?
- How much capital drawdown should we expect?
- Does the strategy generate enough trades to be practical?
- Are the wins large enough to compensate for the losses?
