"""
This module provides decorators for various purposes:

- :py:deco:`measure_time` - Measure the execution time of a function and print it with the given print function
- :py:deco:`handle_error` - Handle an error with different log levels
- :py:deco:`timeout` - Raise an exception if the function runs longer than the specified timeout
- :py:deco:`retry` - Retry a function when specific exceptions are raised, with configurable delay and max attempts
- :py:deco:`simple_cache` - Easy cache function with parameter caching method
- :py:deco:`abstract` - Mark a function as abstract, using :py:class:`~error_handling.LogLevels` for error handling
- :py:deco:`deprecated` - Mark a function as deprecated, using :py:class:`~error_handling.LogLevels` for warning handling
- :py:deco:`silent` - Make a function silent, on stdout and optionally stderr (alternative to :py:class:`stouputils.ctx.Muffle`)

.. code-block:: python

	import time
	import stouputils as stp

	# Print how long each call takes, and remember results so a repeated call is instant
	@stp.measure_time
	@stp.simple_cache
	def slow_square(x: int) -> int:
		time.sleep(0.5)
		return x * x

	slow_square(12)
	slow_square(12)

	# On a ConnectionError, call again up to 5 times, waiting 0.3 seconds in between
	attempts = 0

	@stp.retry(exceptions=ConnectionError, max_attempts=5, delay=0.3)
	def fetch() -> str:
		global attempts
		attempts += 1
		if attempts < 3:
			raise ConnectionError("Busy")
		return "<html>"

	stp.info("Fetched", fetch())

	# Turn an error into a warning instead of stopping the program
	@stp.handle_error(error_log=stp.LogLevels.WARNING)
	def read_port(text: str) -> int:
		return int(text)

	read_port("abc")

	# Warn whoever still calls an old function
	@stp.deprecated(message="Use fetch() instead")
	def download() -> str:
		return fetch()

	download()

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module.svg
  :alt: Terminal output of the example, with timings, retries and warnings
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .abstraction import (
	abstract as abstract,
)
from .caching import (
	CACHE_CLEARERS as CACHE_CLEARERS,
	clear_simple_caches as clear_simple_caches,
	simple_cache as simple_cache,
)
from .common import (
	WRAPPED_ATTRIBUTE as WRAPPED_ATTRIBUTE,
	get_function_name as get_function_name,
	get_wrapper_name as get_wrapper_name,
	safe_wraps as safe_wraps,
	set_wrapper_name as set_wrapper_name,
)
from .deprecation import (
	deprecated as deprecated,
)
from .error_handling import (
	LogLevels as LogLevels,
	handle_error as handle_error,
	report_error as report_error,
)
from .retrying import (
	RetryPolicy as RetryPolicy,
	retry as retry,
	retry_warning as retry_warning,
)
from .silencing import (
	silent as silent,
)
from .timeouts import (
	run_in_thread as run_in_thread,
	run_with_alarm as run_with_alarm,
	timeout as timeout,
)
from .timing import (
	measure_time as measure_time,
)

