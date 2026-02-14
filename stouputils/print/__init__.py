"""
This module provides utility functions for printing messages with different levels of importance.

If a message is printed multiple times, it will be displayed as "(xN) message"
where N is the number of times the message has been printed.

The module also includes a :py:func:`colored` function that formats text with Python 3.14 style coloring
for file paths, line numbers, function names (in magenta), and exception names (in bold magenta).
All functions have their colored counterparts with a 'c' suffix (e.g., :py:func:`infoc`, :py:func:`debugc`, etc.)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/print_module.gif
  :alt: stouputils print examples
"""

# Imports
from .color_formatting import *
from .common import *
from .debugging import *
from .message import *
from .output_stream import *
from .progress_bar import *
from .utils import *

# Test the print functions
if __name__ == "__main__":
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

