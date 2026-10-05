"""
This module provides context managers for various utilities such as logging to a file,
measuring execution time, silencing output, and setting multiprocessing start methods.

- :py:class:`~log_to_file.LogToFile` - Context manager to log to a file every print call (with LINE_UP handling)
- :py:class:`~measure_time.MeasureTime` - Context manager to measure execution time of a code block
- :py:class:`~muffle.Muffle` - Silences output and can replay it on error (alternative to :py:deco:`~stouputils.decorators.silent`)
- :py:class:`~do_nothing.DoNothing` - Context manager that does nothing (no-op)
- :py:class:`~set_mp_start_method.SetMPStartMethod` - Context manager to temporarily set multiprocessing start method

.. code-block:: python

	import time
	import stouputils as stp

	# Everything printed inside this block also goes to run.log
	with stp.LogToFile("run.log"):
		stp.info("Training started")

		# Print how long the indented block took
		with stp.MeasureTime(stp.progress, "Loading the dataset"):
			time.sleep(0.6)

		# Hide everything printed inside this block
		with stp.Muffle():
			print("A chatty library prints this, nobody sees it")

		stp.warning("Validation loss went up")

	stp.info("Content of run.log:")
	print(stp.read_file("run.log"))

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/ctx_module.svg
  :alt: Terminal output of the example, the log file holding the same lines
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .common import (
	AbstractBothContextManager as AbstractBothContextManager,
)
from .do_nothing import (
	DoNothing as DoNothing,
	NullContextManager as NullContextManager,
)
from .log_to_file import (
	ROUTING_LOCK as ROUTING_LOCK,
	LogToFile as LogToFile,
)
from .measure_time import (
	MeasureTime as MeasureTime,
)
from .muffle import (
	ErrorLevelDetector as ErrorLevelDetector,
	Muffle as Muffle,
)
from .set_mp_start_method import (
	SetMPStartMethod as SetMPStartMethod,
)

