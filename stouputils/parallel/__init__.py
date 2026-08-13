"""
This module provides utility functions for parallel processing, such as:

- :py:func:`~multi.multiprocessing`: Execute a function in parallel using multiprocessing
- :py:func:`~multi.multithreading`: Execute a function in parallel using multithreading
- :py:func:`~subprocess.run_in_subprocess`: Execute a function in a subprocess with args and kwargs

I highly encourage you to read the function docstrings to understand when to use each method.

Priority (nice) mapping for :py:func:`~multi.multiprocessing`:

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

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.parallel.capturer",
	"stouputils.parallel.common",
	"stouputils.parallel.multi",
	"stouputils.parallel.subprocess",
})

# Imports
from .capturer import (
	CaptureOutput as CaptureOutput,
	PipeWriter as PipeWriter,
)
from .common import (
	CPU_COUNT as CPU_COUNT,
	delayed_call as delayed_call,
	handle_parameters as handle_parameters,
	nice_wrapper as nice_wrapper,
	normalize_parallel_params as normalize_parallel_params,
	resolve_process_title as resolve_process_title,
	run_sequential as run_sequential,
	set_process_priority as set_process_priority,
	starmap as starmap,
)
from .multi import (
	capture_subprocess_output as capture_subprocess_output,
	doctest_slow as doctest_slow,
	doctest_square as doctest_square,
	multiprocessing as multiprocessing,
	multithreading as multithreading,
	process_title_wrapper as process_title_wrapper,
)
from .subprocess import (
	RemoteSubprocessError as RemoteSubprocessError,
	run_in_subprocess as run_in_subprocess,
)

