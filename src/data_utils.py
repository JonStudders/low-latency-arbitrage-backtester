# src/data_utils.py

## Imports
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime

## Functions
def _safe_download(ticker: str, start_naive, end_naive) -> pd.Series:
	"""
	Internal function to download close prices for a single ticker.

	Args:
		ticker : str
			The ticker symbol of the asset to download prices for.
		start_naive
			Start naive datetime for the data date range
		end_naive
			End naive datetime for the data date range.

	Returns:
		pd.Series
			A pandas Series of adjusted close prices indexed by datetime.
            Returns an empty Series if data retrieval fails or no data exists.
	"""
	try:
		data = yf.download(
			ticker,
			start=start_naive,
			end=end_naive,
			progress=False, # Keep logs clean.
			auto_adjust=True
		)["Close"] # Close price is automatically adjusted for splits and dividends.

		if data.empty:
			print (f"No data returned for ticker: '{ticker}'.")
			return pd.Series(dtype=float)
		
		return data
	except Exception as e:
		print (f"Failed to download data for ticker: '{ticker}': {e}")
		return pd.Series(dtype=float)

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
	
	# Define date range if not specified.
	now = datetime.now(pytz.UTC)
	if end is None:
		end = now
	if start is None:
		start = now.replace(year=now.year - 5)

	# Convert to naive UTC dateimes for yFinance.
	start_naive = start.astimezone(pytz.UTC).replace(tzinfo=None)
	end_naive = end.astimezone(pytz.UTC).replace(tzinfo=None)

	# Download data
	a_data = _safe_download(ticker_a, start_naive, end_naive)
	b_data = _safe_download(ticker_b, start_naive, end_naive)

	if a_data.empty or b_data.empty:
		return pd.DataFrame()
	
	df = pd.concat([a_data, b_data], axis=1)
	df.columns = [ticker_a, ticker_b]
	df = df.dropna()
	df.index = pd.to_datetime(df.index).tz_localize(pytz.UTC)

	return df

if __name__ == "__main__":
	df = download_data("SPY", "QQQ")
	df.to_csv("data/SPY_QQQ.csv")
	print("Data saved to data/SPY_QQ.csv")