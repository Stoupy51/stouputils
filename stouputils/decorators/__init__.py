"""
This module provides decorators for various purposes:

- :py:deco:`measure_time` - Measure the execution time of a function and print it with the given print function
- :py:deco:`handle_error` - Handle an error with different log levels
- :py:deco:`timeout` - Raise an exception if the function runs longer than the specified timeout
- :py:deco:`retry` - Retry a function when specific exceptions are raised, with configurable delay and max attempts
- :py:deco:`simple_cache` - Easy cache function with parameter caching method
- :py:deco:`abstract` - Mark a function as abstract, using :py:class:`~handle_error.LogLevels` for error handling
- :py:deco:`deprecated` - Mark a function as deprecated, using :py:class:`~handle_error.LogLevels` for warning handling
- :py:deco:`silent` - Make a function silent (disable stdout, and stderr if specified) (alternative to :py:class:`stouputils.ctx.Muffle`)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_1.gif
  :alt: stouputils decorators examples

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_2.gif
  :alt: stouputils decorators examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.decorators.common",
})

# Imports
from .abstract import (
	abstract as abstract,
)
from .common import (
	WRAPPED_ATTRIBUTE as WRAPPED_ATTRIBUTE,
	get_function_name as get_function_name,
	get_wrapper_name as get_wrapper_name,
	safe_wraps as safe_wraps,
	set_wrapper_name as set_wrapper_name,
)
from .deprecated import (
	deprecated as deprecated,
)
from .handle_error import (
	LogLevels as LogLevels,
	handle_error as handle_error,
)
from .measure_time import (
	measure_time as measure_time,
)
from .retry import (
	retry as retry,
)
from .silent import (
	silent as silent,
)
from .simple_cache import (
	ALL_CACHES as ALL_CACHES,
	KWARGS_MARKER as KWARGS_MARKER,
	MISSING as MISSING,
	clear_simple_caches as clear_simple_caches,
	simple_cache as simple_cache,
)
from .timeout import (
	timeout as timeout,
)

