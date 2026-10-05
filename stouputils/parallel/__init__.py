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

.. code-block:: python

	import time
	import stouputils as stp

	def slow_square(x: int) -> int:
		time.sleep(0.4)  # Pretend this takes a while
		return x * x

	# Needed because each new process imports this file again
	if __name__ == "__main__":
		# 4 processes at once, with a progress bar (best for heavy computations)
		squares = stp.multiprocessing(slow_square, range(12), desc="Squaring", max_workers=4)
		stp.info("Squares:", squares)

		# 5 threads at once (best for waiting on files or the network)
		stp.multithreading(time.sleep, [0.2] * 20, desc="Waiting on IO", max_workers=5)

		# One call in a separate process, its result sent back
		stp.info("Ran in a subprocess:", stp.run_in_subprocess(slow_square, 7))

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/parallel_module.svg
  :alt: Terminal output of the example, with the progress bars filling up
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

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
	run_pool as run_pool,
	wrap_for_workers as wrap_for_workers,
)
from .subprocess import (
	RemoteSubprocessError as RemoteSubprocessError,
	kill_process_tree as kill_process_tree,
	run_in_subprocess as run_in_subprocess,
	unpack_payload as unpack_payload,
	wait_for_payload as wait_for_payload,
)

