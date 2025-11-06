## Project Roadmap

This project follows a phased development approach, building from statistical research to production-ready infrastructure.

### Phase 1: Statistical Foundation (Complete)
- [x] Data download and alignment (`data_utils.py`)
- [x] Hedge ratio and spread calculation (`preprocess.py`)
- [x] Z-score normalization (`preprocess.py`)
- [x] Signal generation logic (`signals.py`)
- [x] Threshold analysis experiments
- [x] Comprehensive test suite (22 tests, 100% coverage)

### Phase 2: Backtesting & Metrics (In Progress)
- [x] Test-driven backtest specification (`test_backtest.py`)
- [ ] Backtest implementation (`backtest.py`)
- [ ] Performance metrics (Sharpe, drawdown, win rate)
- [ ] Equity curve visualization

### Phase 3: Real-Time Prototype (Planned)
- [ ] Live data stream integration
- [ ] Real-time signal generation engine
- [ ] Position tracking and PnL monitoring
- [ ] Alert system for extreme moves

### Phase 4: Production Optimization (Planned)
- [ ] C++ spread/z-score calculation kernel
- [ ] C++ backtest engine
- [ ] pybind11 Python bindings
- [ ] Performance benchmarking (target: <1ms latency)
- [ ] Monitoring dashboard
- [ ] Docker deployment