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

# Imports
from .abstract import *
from .common import *
from .deprecated import *
from .handle_error import *
from .measure_time import *
from .retry import *
from .silent import *
from .simple_cache import *
from .timeout import *

