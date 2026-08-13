"""
This module provides decorators for various purposes:

- :py:deco:`measure_time` - Measure the execution time of a function and print it with the given print function
- :py:deco:`handle_error` - Handle an error with different log levels
- :py:deco:`timeout` - Raise an exception if the function runs longer than the specified timeout
- :py:deco:`retry` - Retry a function when specific exceptions are raised, with configurable delay and max attempts
- :py:deco:`simple_cache` - Easy cache function with parameter caching method
- :py:deco:`abstract` - Mark a function as abstract, using :py:class:`~error_handling.LogLevels` for error handling
- :py:deco:`deprecated` - Mark a function as deprecated, using :py:class:`~error_handling.LogLevels` for warning handling
- :py:deco:`silent` - Make a function silent (disable stdout, and stderr if specified) (alternative to :py:class:`stouputils.ctx.Muffle`)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_1.gif
  :alt: stouputils decorators examples

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_2.gif
  :alt: stouputils decorators examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .abstraction import (
	abstract as abstract,
)
from .caching import (
	ALL_CACHES as ALL_CACHES,
	KWARGS_MARKER as KWARGS_MARKER,
	MISSING as MISSING,
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
)
from .retrying import (
	retry as retry,
)
from .silencing import (
	silent as silent,
)
from .timeouts import (
	timeout as timeout,
)
from .timing import (
	measure_time as measure_time,
)

