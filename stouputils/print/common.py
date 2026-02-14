
# Imports
import os
import time
from typing import Any

from ..config import StouputilsConfig as Cfg

# Backwards compatibility for constants
RESET: str      = Cfg.RESET
RED: str        = Cfg.RED
GREEN: str      = Cfg.GREEN
YELLOW: str     = Cfg.YELLOW
BLUE: str       = Cfg.BLUE
MAGENTA: str    = Cfg.MAGENTA
CYAN: str       = Cfg.CYAN
LINE_UP: str    = Cfg.LINE_UP
BOLD: str       = Cfg.BOLD
BAR_FORMAT: str = Cfg.BAR_FORMAT

# Enable colors on Windows 10 terminal if applicable
if os.name == "nt":
	import subprocess
	subprocess.run("color", shell=True)

# Shared memory for print functions
class PrintMemory:
	""" Class to store shared variables for print functions. """
	previous_args_kwards: tuple[Any, Any] = ((), {})
	""" Store the previous print call's args and kwargs for comparison in is_same_print() """
	nb_values: int = 1
	""" Count how many times the same value has been printed in a row for is_same_print() """
	import_time: float = time.time()
	""" Store the import time to determine how to format timestamps in current_time() """

