# tests/test_data_utils.py

## Imports
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from src.data_utils import download_data, _safe_download


## Helpers
def fake_yfinance_download(ticker, start, end, progress=False, auto_adjust=True):
	"""
	Fake version of yfinance.download() for testing.
	Returns small deterministic 'Close' price data.
	"""
	date_range = pd.date_range(start, end, freq="D")
	data = pd.DataFrame(
		{"Close": np.linspace(100, 110, len(date_range)) + (0 if ticker == "SPY" else 5)},
		index=date_range,
	)
	return data


## Tests

def test_valid_tickers_returns_dataframe(monkeypatch):
	"""
	Valid tickers should return a non-empty DataFrame.
	"""
	# Arrange: Mock yfinance.download() to avoid real API calls
	import yfinance as yf
	monkeypatch.setattr(yf, "download", fake_yfinance_download)

	# Act: Fetch SPY and QQQ assets
	df = download_data("SPY", "QQQ")

	# Assert: Validate type and content
	assert isinstance(df, pd.DataFrame), "Expected pandas DataFrame type."
	assert not df.empty, "DataFrame should not be empty."
	assert list(df.columns) == ["SPY", "QQQ"], "Expected headers to match tickers."


def test_safe_download_invalid_ticker_returns_empty(monkeypatch):
	"""
	Invalid ticker should return an empty Series.
	"""
	# Arrange: Mock yfinance.download() to raise an exception for invalid tickers
	import yfinance as yf
	def fake_fail(*args, **kwargs):
		raise ValueError("Invalid ticker")
	monkeypatch.setattr(yf, "download", fake_fail)

	# Set up date range for data download
	end_date = datetime.now(pytz.UTC)
	start_date = end_date - timedelta(days=5)
	start_naive = start_date.replace(tzinfo=None)
	end_naive = end_date.replace(tzinfo=None)

	# Act: Attempt invalid ticker download
	series = _safe_download("ABCDE", start_naive, end_naive)

	# Assert: Invalid ticker should return empty Series
	assert series.empty, "Expected empty Series for invalid ticker."


def test_invalid_ticker_returns_empty_dataframe(monkeypatch):
	"""
	Invalid tickers should return an empty DataFrame.
	"""
	# Arrange: Mock yfinance.download() to fail when called
	import yfinance as yf
	def fake_fail(*args, **kwargs):
		raise ValueError("Invalid ticker")
	monkeypatch.setattr(yf, "download", fake_fail)

	# Act: Attempt invalid ticker pair download
	df = download_data("ABCDE", "QQQ")

	# Assert: Invalid ticker should return empty DataFrame
	assert df.empty, "Expected empty DataFrame for invalid ticker."


def test_index_is_timezone_aware(monkeypatch):
	"""
	Ensure DataFrame index is standardised to UTC.
	"""
	# Arrange: Mock yfinance.download() to avoid real API calls
	import yfinance as yf
	monkeypatch.setattr(yf, "download", fake_yfinance_download)

	# Act: Download data for SPY and QQQ
	df = download_data("SPY", "QQQ")

	# Assert: Validate timezone is set to UTC
	assert df.index.tz is not None, "Expected timezone to be implemented."
	assert str(df.index.tz) == "UTC", "Expected index timezone to be UTC."


def test_default_data_range_is_recent(monkeypatch):
	"""
	Ensure download_data uses a 5 year window by default.
	"""
	# Arrange: Mock yfinance.download() to avoid real API calls
	import yfinance as yf
	monkeypatch.setattr(yf, "download", fake_yfinance_download)

	# Act: Download data without specifying date range (uses defaults)
	df = download_data("SPY", "QQQ")

	# Assert: Validate date range is approximately 5 years
	start_date = df.index.min()
	end_date = df.index.max()
	now = datetime.now(pytz.UTC)

	assert (now.year - start_date.year) <= 6, "Start date should be roughly 5 years ago."
	assert end_date <= now, "End date should not be in the future."
