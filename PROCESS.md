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
