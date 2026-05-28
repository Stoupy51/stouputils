
# Imports
import re
import time
from typing import Any

from .common import PrintMemory


# Utility functions
def remove_colors(text: str) -> str:
	r""" Remove the colors from a text.
	See :py:func:`remove_ansi` to remove all ANSI escape sequences

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
	return remove_ansi(text, pattern=r'\x1b\[[0-9;]*m')


def remove_ansi(text: str, pattern: str = r'\x1b\[[0-?]*[ -/]*[@-~]') -> str:
	r""" Remove all ANSI escape sequences from a text.
	See :py:func:`remove_colors` to remove only color codes.

	>>> remove_ansi("\x1b[91mHello\x1b[0m")
	'Hello'
	>>> remove_ansi("\x1b[1m\x1b[95mBold Magenta Text\x1b[0m")
	'Bold Magenta Text'
	>>> remove_ansi("No ANSI here")
	'No ANSI here'
	>>> remove_ansi("\x1b[91mRed\x1b[0m and \x1b[92mGreen\x1b[0m")
	'Red and Green'
	>>> remove_ansi("Line 1\x1b[1ALine 2")
	'Line 1Line 2'
	>>> remove_ansi("Hello\x1b[2JWorld")
	'HelloWorld'
	"""
	return re.sub(pattern, '', text)

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

