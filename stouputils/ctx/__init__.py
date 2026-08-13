"""
This module provides context managers for various utilities such as logging to a file,
measuring execution time, silencing output, and setting multiprocessing start methods.

- :py:class:`~log_to_file.LogToFile` - Context manager to log to a file every print call (with LINE_UP handling)
- :py:class:`~measure_time.MeasureTime` - Context manager to measure execution time of a code block
- :py:class:`~muffle.Muffle` - Context manager that temporarily silences output, optionally replaying it only on error (alternative to :py:deco:`~stouputils.decorators.silent`)
- :py:class:`~do_nothing.DoNothing` - Context manager that does nothing (no-op)
- :py:class:`~set_mp_start_method.SetMPStartMethod` - Context manager to temporarily set multiprocessing start method

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/ctx_module.gif
  :alt: stouputils ctx examples
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

