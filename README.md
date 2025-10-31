# Jon Studders - low-latency-arbitrage-backtester

A high-performance statistical arbitrage system designed for pair-trading highly correlated assets, including equities, index products, and commodity futures. The engine uses Python for backtesting and statistical modelling, with the critical, low-latency Z-score signal generation kernel implemented and optimised in C++ using pybind11.

## Project Goals

This project was developed to demonstrate expertise in statistical arbitrage across diverse asset classes, including:
- Equities: Visa (V) vs. Mastercard (MA), and Alphabet (GOOGL) vs. Meta Platforms (META).
- Index Products: S&P 500 ETF (SPY) vs. Nasdaq 100 ETF (QQQ).
- Commodity Futures: WTI Crude Oil Futures vs. Brent Crude Oil Futures.

The technical focus remains on three key areas:
1. Statistical Modelling: Implementing a mean-reversion strategy based on the relationship between two correlated financial assets.
2. Financial Domain Knowledge: Applying the strategy to pair trading across different markets and calculating standard backtesting metrics (Sharpe Ratio, Max Drawdown).
3. Low-Latency Optimisation: Offloading the high-frequency calculation of the rolling Z-score to a dedicated C++ kernel to simulate real-time performance requirements.

## Technology Stack

### Python:
- Lib 1
- Lib 2

### C++:
- Lib 1
- Lib 2