
# Imports
import re
import time
from typing import Any

from .common import PrintMemory


# Utility functions
def remove_colors(text: str) -> str:
    r""" Remove the colors from a text

	>>> remove_colors("\x1b[91mHello\x1b[0m")
	'Hello'
	>>> remove_colors("\x1b[1m\x1b[95mBold Magenta Text\x1b[0m")
	'Bold Magenta Text'
	>>> remove_colors("No colors here")
	'No colors here'
	>>> remove_colors("\x1b[91mRed\x1b[0m and \x1b[92mGreen\x1b[0m")
	'Red and Green'

	Other ANSI escape codes (e.g., cursor movement) are not removed since they are not colors:
	>>> remove_colors("Line 1\x1b[1ALine 2 \x1b[31mRed Text\x1b[0m")
	'Line 1\x1b[1ALine 2 Red Text'
	"""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def is_same_print(*args: Any, **kwargs: Any) -> bool:
	""" Checks if the current print call is the same as the previous one. """
	try:
		if PrintMemory.previous_args_kwards == (args, kwargs):
			PrintMemory.nb_values += 1
			return True
	except Exception:
		# Comparison failed (e.g., comparing DataFrames or other complex objects)
		# Use str() for comparison instead
		current_str: str = str((args, kwargs))
		previous_str: str = str(PrintMemory.previous_args_kwards)
		if previous_str == current_str:
			PrintMemory.nb_values += 1
			return True
	# Else, update previous args and reset counter
	PrintMemory.previous_args_kwards = (args, kwargs)
	PrintMemory.nb_values = 1
	return False

def current_time() -> str:
	""" Get the current time as "HH:MM:SS" if less than 24 hours since import, else "YYYY-MM-DD HH:MM:SS" """
	# If the import time is more than 24 hours, return the full datetime
	if (time.time() - PrintMemory.import_time) > (24 * 60 * 60):
		return time.strftime("%Y-%m-%d %H:%M:%S")
	else:
		return time.strftime("%H:%M:%S")

