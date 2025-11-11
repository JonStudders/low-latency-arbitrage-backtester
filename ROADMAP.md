## Project Roadmap

This project follows a phased development approach, building from statistical research to production-ready infrastructure.

### Phase 1: Statistical Foundation (Complete)
- [x] Data download and alignment (`data_utils.py`)
- [x] Hedge ratio and spread calculation (`preprocess.py`)
- [x] Z-score normalisation (`preprocess.py`)
- [x] Signal generation logic (`signals.py`)
- [x] Threshold analysis experiments
- [x] Comprehensive test suite 

### Phase 2: Backtesting & Metrics (Complete)
- [x] Test-driven backtest specification (`test_backtest.py`)
- [x] Backtest implementation (`backtest.py`)
- [x] Performance metrics (Sharpe, drawdown, win rate, profit factor)
- [x] Comprehensive metrics testing 
- [x] Equity curve visualisation

### Phase 3: Parameter Optimisation (Planned)
- [ ] Parameter grid search for lookback, entry_z, exit_z
- [ ] Automated multi-pair backtesting
- [ ] Robustness analysis across pairs
- [ ] Heatmap and surface plots of Sharpe / drawdown stability
- [ ] Identification of stable parameter regions

### Phase 4: Real-Time Prototype (Planned)
- [ ] Live data stream integration
- [ ] Real-time signal generation engine
- [ ] Position tracking and PnL monitoring
- [ ] Alert system for extreme moves

### Phase 5: Production Optimisation (Planned)
- [ ] C++ spread/z-score calculation kernel
- [ ] C++ backtest engine
- [ ] pybind11 Python bindings
- [ ] Performance benchmarking (target: <1 ms latency)
- [ ] Monitoring dashboard
- [ ] Docker deployment