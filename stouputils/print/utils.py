
# Imports
import time
from typing import Any

from ..config import StouputilsConfig as Cfg
from .common import PrintMemory


# Utility functions
def remove_colors(text: str) -> str:
	""" Remove the colors from a text """
	for color in [Cfg.RESET, Cfg.RED, Cfg.GREEN, Cfg.YELLOW, Cfg.BLUE, Cfg.MAGENTA, Cfg.CYAN, Cfg.LINE_UP]:
		text = text.replace(color, "")
	return text

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

