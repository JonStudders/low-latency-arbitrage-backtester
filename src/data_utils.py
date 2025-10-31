# src/data_utils.py

## Imports
import yfinance as yf
import pandas as pd
from datetime import datetime

## Functions
def download_data(
	ticker_a: str, 
	ticker_b: str, 
	start: datetime = None,
	end: datetime = None
) -> pd.DataFrame:
	"""
	Download historical price data for two assets using Yahoo Finance API.

	download_data gets the daily price data of two assets using their ticker
	symbols from Yahoo Finance. It then cleans up the data by making sure the
	dates align between each entries, removing mismatched/missing entries and 
	then return a dataset for modeling.	

	Args:
		ticker_a : str
			The ticker symbol of the first asset.
		ticker_b : str
			The ticker symbol of the second asset.
		start : datetime, optional
			Start datetime with timezone. Defaults to current UTC time - 5yrs.
		end : datetime, optional
			End datetime with timezone. Defaults to current UTC time.

	Returns:
		pd.Dataframe
			A table containing two columns, ticker_a and ticker_b, with
			asset prices alongside corresponding dates as an index.
	
	Example:
		With defined start/end date.
		>>> start = datetime(2020, 1, 1, tzinfo=pytz.UTC)
		>>> end = datetime.now(2025, 1, 1, tzinfo=pytz.UTC)
		>>> dataframe = download_data("SPY", "QQQ", start_date, end_date)

		With default start/end date.
		>>> dataframe = download_data("SPY", "QQQ")
	
	Notes:
		- This function uses Yahoo Finance API through the yFinance library.
		- This function has no effort to retrieve missing entries.
	"""

	return pd.DataFrame()