# tests/test_data_utils.py

## Imports
import pytest
import pandas as pd
from datetime import datetime
import pytz
from src.data_utils import download_data, _safe_download

## Tests

def test_valid_tickers_returns_dataframe():
	"""
	Valid tickers should return a non-empty DataFrame.
	"""

	# Fetch SPY and QQQ assets.
	df = download_data("SPY", "QQQ")

	# Validate type of the varible.
	assert isinstance(df, pd.DataFrame) # Expect pandas DataFrame type.

	# Validate content
	assert not df.empty, "DataFrame should not be empty."
	assert list(df.columns) == ["SPY", "QQQ"], "Expected headers to match tickers."

def test_safe_download_invalid_ticker_returns_empty():

	# Set date range for data download.
	end_date = datetime.now(pytz.UTC)
	start_date = end_date.replace(yea=end_date.year - 5)
	start_naive = start_date.astimezone(pytz.UTC).replace(tzinfo=None)
	end_naive = end_date.astimezone(pytz.UTC).replace(tzinfo=None)

	# Download invalid ticker.
	series = _safe_download("ABCDE", start_naive, end_naive)
	
	# Invalid ticker should return empty data series.
	assert series.empty, "Expected empty Data Series for invalid ticker."

def test_invalid_ticker_returns_empty_dataframe():
	"""
	Invalid tickers should return an empty DataFrame.
	"""

	# Attempt a data fetch with an invalid ticker.
	df = download_data("ABCDE", "QQQ")

	# Invalid ticker should return no data.
	assert df.empty, "Expected empty DataFrame for invalid ticker."

def test_index_is_timezone_aware():
	"""
	Ensure DataFrame is standardised to UTC.
	"""

	# Fetch SPY and QQQ assets.
	df = download_data("SPY", "QQQ")

	assert df.index.tz is not None, "Expected timezone to be implemented."
	assert str(df.index.tz) == "UTC", "Expected index timezone to be UTC."

def test_default_data_range_is_recent():
	"""
	Ensure download_data uses a 5 year window by default.
	"""
	
	# Fetch SPY and QQQ assets.
	df = download_data("SPY", "QQQ")

	# Get earlier and latest date from the DataFrame, and current time.
	start_date = df.index.min()
	end_date = df.index.max()
	now = datetime.now(pytz.UTC)

	# Data should not be older than ~5 years.
	assert (now.year - start_date.year) <= 6, "Start date should be roughly 5 years ago"
	assert end_date <= now, "End date should not be in the future"