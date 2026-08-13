"""
This module provides utility functions for printing messages with different levels of importance.

If a message is printed multiple times, it will be displayed as "(xN) message"
where N is the number of times the message has been printed.

The module also includes a :py:func:`~color_formatting.colored` function that formats text with Python 3.14 style coloring
for file paths, line numbers, function names (in magenta), and exception names (in bold magenta).
All functions have their colored counterparts with a 'c' suffix (e.g., :py:func:`infoc`, :py:func:`debugc`, etc.)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/print_module.gif
  :alt: stouputils print examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"numpy",
	"stouputils.config",
	"stouputils.print.color_formatting",
	"stouputils.print.common",
	"stouputils.print.debugging",
	"stouputils.print.message",
	"stouputils.print.output_stream",
	"stouputils.print.progress_tqdm",
	"stouputils.print.utils",
	"time",
})

# Imports
from .color_formatting import (
	colored as colored,
	format_colored as format_colored,
)
from .common import (
	BAR_FORMAT as BAR_FORMAT,
	BLUE as BLUE,
	BOLD as BOLD,
	CYAN as CYAN,
	GREEN as GREEN,
	LINE_UP as LINE_UP,
	MAGENTA as MAGENTA,
	RED as RED,
	RESET as RESET,
	YELLOW as YELLOW,
	PrintMemory as PrintMemory,
)
from .debugging import (
	breakpoint as breakpoint,
	breakpointc as breakpointc,
	whatisit as whatisit,
	whatisitc as whatisitc,
)
from .message import (
	alt_debug as alt_debug,
	alt_debugc as alt_debugc,
	debug as debug,
	debugc as debugc,
	error as error,
	errorc as errorc,
	info as info,
	infoc as infoc,
	progress as progress,
	progressc as progressc,
	suggestion as suggestion,
	suggestionc as suggestionc,
	warning as warning,
	warningc as warningc,
)
from .output_stream import (
	LINEUP_RE as LINEUP_RE,
	TeeMultiOutput as TeeMultiOutput,
)
from .progress_tqdm import (
	progress_bar as progress_bar,
)
from .utils import (
	current_time as current_time,
	is_same_print as is_same_print,
	remove_ansi as remove_ansi,
	remove_colors as remove_colors,
)

# Test the print functions
if __name__ == "__main__":
	import time

	from ..config import StouputilsConfig as Cfg

	info("Hello", "World")
	time.sleep(0.5)
	info("Hello", "World")
	time.sleep(0.5)
	info("Hello", "World")
	time.sleep(0.5)
	info("Not Hello World !")
	time.sleep(0.5)
	info("Hello", "World")
	time.sleep(0.5)
	info("Hello", "World")

	# All remaining print functions
	alt_debug("Hello", "World")
	debug("Hello", "World")
	suggestion("Hello", "World")
	progress("Hello", "World")
	warning("Hello", "World")
	error("Hello", "World", exit=False)
	whatisit("Hello")
	whatisit("Hello", "World")
	info("Test gray", color=Cfg.GRAY)
	info("Test light gray", color=Cfg.LIGHT_GRAY)
	info("Test reset", color=Cfg.RESET)
	info("Test bold", color=Cfg.BOLD)
	info("Test black", color=Cfg.BLACK)
	info("Test white", color=Cfg.WHITE)

	# Test whatisit with different types
	import numpy as np
	print()
	whatisitc(
		123,
		"Hello World",
		[1, 2, 3, 4, 5],
		np.array([[1, 2, 3], [4, 5, 6]]),
		{"a": 1, "b": 2},
	)

