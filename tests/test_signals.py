# tests/test_signals.py

## Imports
import pytest
import pandas as pd
import numpy as np
from src.signals import generate_trade_signals


## Helper Functions
def make_df(z_values):
	"""
	Create a small DataFrame with a z-score column for testing.
	"""
	return pd.DataFrame({"zscore": z_values})


## Tests

def test_valid_dataframe_generates_signals():
	"""
	Valid DataFrame should return a non-empty DataFrame with a 'signal' column.
	"""
	# Arrange: Create a sample z-score sequence
	z = [0.1, 2.1, 1.9, 0.0, -2.3, -1.0, 0.0]
	df = make_df(z)

	# Act: Run signal generation
	result = generate_trade_signals(df, entry_z=2.0, exit_z=0.5)

	# Assert: Validate type and structure
	assert isinstance(result, pd.DataFrame), "Expected a pandas DataFrame."
	assert "signal" in result.columns, "Missing 'signal' column in output."
	assert not result.empty, "Output DataFrame should not be empty."


def test_entry_and_exit_behavior():
	"""
	Ensure signals enter and exit positions correctly based on z-score thresholds.
	"""
	# Arrange: Create z-score sequence with both long and short entries
	z = [0.1, 2.1, 1.9, 0.0, -2.3, -1.0, 0.0]
	df = make_df(z)
	
	# Act: Generate signals with entry and exit thresholds
	result = generate_trade_signals(df, entry_z=2.0, exit_z=0.5)

	# Assert: Verify expected signal pattern
	# - Short when z > +2
	# - Long when z < -2
	# - Flat when |z| <= 0.5
	expected = [0, -1, -1, 0, 1, 1, 0]
	assert result["signal"].tolist() == expected, "Signal pattern does not match expected behaviour."


def test_forward_fill_maintains_position():
	"""
	Ensure open positions remain until exit condition is met.
	"""
	# Arrange: Create z-score sequence that stays above exit band after entry
	z = [0.0, 2.2, 1.8, 1.5, 0.4]
	df = make_df(z)
	
	# Act: Generate signals
	result = generate_trade_signals(df, entry_z=2.0, exit_z=0.5)

	# Assert: Should remain short until z <= 0.5 (exit band)
	expected = [0, -1, -1, -1, 0]
	assert result["signal"].tolist() == expected, "Forward-fill logic failed to maintain position."


def test_negative_zscore_creates_long_signal():
	"""
	Ensure negative z-scores trigger long positions symmetrically.
	"""
	# Arrange: Create z-score sequence that crosses below -entry_z
	z = [0.0, -2.1, -1.5, -0.3]
	df = make_df(z)
	
	# Act: Generate signals
	result = generate_trade_signals(df, entry_z=2.0, exit_z=0.5)

	# Assert: Verify long signals are created for negative z-scores
	expected = [0, 1, 1, 0]
	assert result["signal"].tolist() == expected, "Negative z-score side not handled symmetrically."


def test_threshold_validation():
	"""
	Ensure entry threshold is strictly greater than exit threshold.
	"""
	# Arrange: Create a simple DataFrame and set entry_z equal to exit_z (invalid)
	df = make_df([0.0, 1.0])
	
	# Act & Assert: Function should raise ValueError when entry_z <= exit_z
	with pytest.raises(ValueError):
		generate_trade_signals(df, entry_z=1.0, exit_z=1.0)


def test_missing_column_raises_error():
	"""
	Ensure missing z-score column raises ValueError.
	"""
	# Arrange: Create a DataFrame without the required 'zscore' column
	df = pd.DataFrame({"wrong_col": [0, 1, 2]})
	
	# Act & Assert: Function should raise ValueError for missing column
	with pytest.raises(ValueError):
		generate_trade_signals(df)


def test_nan_values_do_not_break_signal_generation():
	"""
	Ensure NaN values do not cause new entries or invalid states.
	"""
	# Arrange: Create z-score sequence with NaN values
	z = [np.nan, 2.2, np.nan, 2.3, np.nan, 0.0]
	df = make_df(z)
	
	# Act: Generate signals
	result = generate_trade_signals(df, entry_z=2.0, exit_z=0.5)

	# Assert: NaN values should not break signal continuity
	expected = [0, -1, -1, -1, -1, 0]
	assert result["signal"].tolist() == expected, "NaN handling failed to preserve expected pattern."
