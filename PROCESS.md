# Process Reference
This document explains the end-to-end workflow of the pairs trading pipeline in plain English.  
It provides a step-by-step outline of how data is downloaded, processed, and transformed into standardized trading signals.

---

## Process 1 — Data Download
Implemented in: `/src/data_utils.py`

We download historical price data for two assets using **Yahoo Finance** (`yfinance`).  
The goal is to collect clean, time-aligned data that can be compared directly between both assets.

**Steps performed:**
1. Download both asset price series over a consistent time window.  
2. Align timestamps so that every date has valid prices for both assets.  
3. Handle missing data by removing or forward-filling small gaps to prevent misalignment.  
4. Convert all timestamps to **UTC** to ensure both datasets share the same timezone reference.

This process ensures the dataset is synchronized and reliable before any statistical analysis.

---

## Process 2 — Spread Calculation
Implemented in: `/src/preprocess.py`

Once both price series are aligned, we measure how far they move relative to one another.

### Hedge Ratio (β)
The hedge ratio adjusts for differences in scale or volatility between the two assets.  
It is estimated using a **rolling regression** of one asset against the other:

\[
β_t = \frac{\text{Cov}(A_t, B_t)}{\text{Var}(B_t)}
\]

This represents how much Asset A typically moves for every 1-unit move in Asset B over the last *N* observations (default = 60).  
It normalizes the relationship so we can compare relative movements rather than raw prices.

### Spread
The spread quantifies how far apart the two normalized prices are:

\[
Spread_t = A_t - β_t \times B_t
\]

- If the spread widens, one asset has become expensive relative to the other.  
- If the spread narrows, the pair is converging back toward equilibrium.

The spread captures relative mispricing and forms the foundation of the pairs trading strategy.

---

## Process 3 — Z-Score Normalization
Implemented in: `/src/preprocess.py`

We standardize the spread into a **z-score** to measure how unusual the current spread is compared to its recent history.

\[
Z_t = \frac{Spread_t - \text{Mean}(Spread_{t-N:t})}{\text{Std}(Spread_{t-N:t})}
\]

- \(Z_t = 0\): the pair is balanced (normal relationship)  
- \(Z_t > +2\): the spread is unusually wide (potential short signal)  
- \(Z_t < -2\): the spread is unusually narrow (potential long signal)

The z-score converts spreads into a consistent statistical scale, allowing all asset pairs to be compared on equal terms.
