"""
This module provides utility functions for parallel processing, such as:

- :py:func:`~stouputils.parallel.multi.multiprocessing`: Execute a function in parallel using multiprocessing
- :py:func:`~stouputils.parallel.multi.multithreading`: Execute a function in parallel using multithreading
- :py:func:`~stouputils.parallel.subprocess.run_in_subprocess`: Execute a function in a subprocess with args and kwargs

I highly encourage you to read the function docstrings to understand when to use each method.

Priority (nice) mapping for :py:func:`~stouputils.parallel.multi.multiprocessing`:

- Unix-style values from -20 (highest priority) to 19 (lowest priority)
- Windows automatic mapping:
  * -20 to -10: HIGH_PRIORITY_CLASS
  * -9 to -1: ABOVE_NORMAL_PRIORITY_CLASS
  * 0: NORMAL_PRIORITY_CLASS
  * 1 to 9: BELOW_NORMAL_PRIORITY_CLASS
  * 10 to 19: IDLE_PRIORITY_CLASS

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/parallel_module.gif
  :alt: stouputils parallel examples
"""

# Imports
from .capturer import *
from .common import *
from .multi import *
from .subprocess import *

