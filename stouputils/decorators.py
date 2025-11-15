"""
This module provides decorators for various purposes:

- measure_time(): Measure the execution time of a function and print it with the given print function
- handle_error(): Handle an error with different log levels
- simple_cache(): Easy cache function with parameter caching method
- retry(): Retry a function when specific exceptions are raised, with configurable delay and max attempts
- abstract(): Mark a function as abstract, using LogLevels for error handling
- deprecated(): Mark a function as deprecated, using LogLevels for warning handling
- silent(): Make a function silent (disable stdout, and stderr if specified) (alternative to stouputils.ctx.Muffle)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_1.gif
  :alt: stouputils decorators examples

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_2.gif
  :alt: stouputils decorators examples
"""

# Imports
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from pickle import dumps as pickle_dumps
from traceback import format_exc
from typing import Any, Literal

from .ctx import MeasureTime, Muffle
from .print import debug, error, warning


# Execution time decorator
def measure_time(
	print_func: Callable[..., None] = debug,
	message: str = "",
	perf_counter: bool = True,
	is_generator: bool = False
) -> Callable[..., Any]:
	""" Decorator that will measure the execution time of a function and print it with the given print function

	Args:
		print_func		(Callable):	Function to use to print the execution time (e.g. debug, info, warning, error, etc.)
		message			(str):		Message to display with the execution time (e.g. "Execution time of Something"),
			defaults to "Execution time of {func.__name__}"
		perf_counter	(bool):		Whether to use time.perf_counter_ns or time.time_ns
			defaults to True (use time.perf_counter_ns)
		is_generator	(bool):		Whether the function is a generator or not (default: False)
			When True, the decorator will yield from the function instead of returning it.

	Returns:
		Callable:	Decorator to measure the time of the function.

	Examples:
		.. code-block:: python

			> @measure_time(info)
			> def test():
			>     pass
			> test()  # [INFO HH:MM:SS] Execution time of test: 0.000ms (400ns)
	"""
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

		# Set the message if not specified, else use the provided one
		new_msg: str = message if message else f"Execution time of {_get_func_name(func)}"

		if is_generator:
			@wraps(func)
			def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
				with MeasureTime(print_func=print_func, message=new_msg, perf_counter=perf_counter):
					yield from func(*args, **kwargs)
		else:
			@wraps(func)
			def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
				with MeasureTime(print_func=print_func, message=new_msg, perf_counter=perf_counter):
					return func(*args, **kwargs)
		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.measure_time", func)
		return wrapper
	return decorator

# Decorator that handle an error with different log levels
class LogLevels(Enum):
	""" Log level for the errors in the decorator handle_error() """
	NONE = 0
	""" Do nothing """
	WARNING = 1
	""" Show as warning """
	WARNING_TRACEBACK = 2
	""" Show as warning with traceback """
	ERROR_TRACEBACK = 3
	""" Show as error with traceback """
	RAISE_EXCEPTION = 4
	""" Raise exception """

force_raise_exception: bool = False
""" If true, error_log parameter will be set to RAISE_EXCEPTION for every next handle_error calls, useful for doctests """

def handle_error(
	func: Callable[..., Any] | None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0
) -> Callable[..., Any]:
	""" Decorator that handle an error with different log levels.

	Args:
		func        (Callable[..., Any] | None):    	Function to decorate
		exceptions	(tuple[type[BaseException]], ...):	Exceptions to handle
		message		(str):								Message to display with the error. (e.g. "Error during something")
		error_log	(LogLevels):						Log level for the errors
			LogLevels.NONE:					None
			LogLevels.WARNING:				Show as warning
			LogLevels.WARNING_TRACEBACK:	Show as warning with traceback
			LogLevels.ERROR_TRACEBACK:		Show as error with traceback
			LogLevels.RAISE_EXCEPTION:		Raise exception
		sleep_time	(float):							Time to sleep after the error (e.g. 0.0 to not sleep, 1.0 to sleep for 1 second)

	Examples:
		>>> @handle_error
		... def might_fail():
		...     raise ValueError("Let's fail")

		>>> @handle_error(error_log=LogLevels.WARNING)
		... def test():
		...     raise ValueError("Let's fail")
		>>> # test()	# [WARNING HH:MM:SS] Error during test: (ValueError) Let's fail
	"""
	# Update error_log if needed
	if force_raise_exception:
		error_log = LogLevels.RAISE_EXCEPTION

	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		if message != "":
			msg: str = f"{message}, "
		else:
			msg: str = message

		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			try:
				return func(*args, **kwargs)
			except exceptions as e:
				if error_log == LogLevels.WARNING:
					warning(f"{msg}Error during {_get_func_name(func)}: ({type(e).__name__}) {e}")
				elif error_log == LogLevels.WARNING_TRACEBACK:
					warning(f"{msg}Error during {_get_func_name(func)}:\n{format_exc()}")
				elif error_log == LogLevels.ERROR_TRACEBACK:
					error(f"{msg}Error during {_get_func_name(func)}:\n{format_exc()}", exit=True)
				elif error_log == LogLevels.RAISE_EXCEPTION:
					raise e

				# Sleep for the specified time, only if the error_log is not ERROR_TRACEBACK (because it's blocking)
				if sleep_time > 0.0 and error_log != LogLevels.ERROR_TRACEBACK:
					time.sleep(sleep_time)
		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.handle_error", func)
		return wrapper

	# Handle both @handle_error and @handle_error(exceptions=..., message=..., error_log=...)
	if func is None:
		return decorator
	return decorator(func)

# Easy cache function with parameter caching method
def simple_cache(
	func: Callable[..., Any] | None = None,
	*,
	method: Literal["str", "pickle"] = "str"
) -> Callable[..., Any]:
	""" Decorator that caches the result of a function based on its arguments.

	The str method is often faster than the pickle method (by a little) but not as accurate with complex objects.

	Args:
		func   (Callable[..., Any] | None): Function to cache
		method (Literal["str", "pickle"]):  The method to use for caching.
	Returns:
		Callable[..., Any]: A decorator that caches the result of a function.
	Examples:
		>>> @simple_cache
		... def test1(a: int, b: int) -> int:
		...     return a + b

		>>> @simple_cache(method="str")
		... def test2(a: int, b: int) -> int:
		...     return a + b
		>>> test2(1, 2)
		3
		>>> test2(1, 2)
		3
		>>> test2(3, 4)
		7
	"""
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		# Create the cache dict
		cache_dict: dict[bytes, Any] = {}

		# Create the wrapper
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:

			# Get the hashed key
			if method == "str":
				hashed: bytes = str(args).encode() + str(kwargs).encode()
			elif method == "pickle":
				hashed: bytes = pickle_dumps((args, kwargs))
			else:
				raise ValueError("Invalid caching method. Supported methods are 'str' and 'pickle'.")

			# If the key is in the cache, return it
			if hashed in cache_dict:
				return cache_dict[hashed]

			# Else, call the function and add the result to the cache
			else:
				result: Any = func(*args, **kwargs)
				cache_dict[hashed] = result
				return result

		# Return the wrapper
		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.simple_cache", func)
		return wrapper

	# Handle both @simple_cache and @simple_cache(method=...)
	if func is None:
		return decorator
	return decorator(func)

# Decorator that retries a function when specific exceptions are raised
def retry(
	func: Callable[..., Any] | None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	max_attempts: int = 10,
	delay: float = 1.0,
	backoff: float = 1.0
) -> Callable[..., Any]:
	""" Decorator that retries a function when specific exceptions are raised.

	Args:
		func			(Callable[..., Any] | None):			Function to retry
		exceptions		(tuple[type[BaseException], ...]):		Exceptions to catch and retry on
		max_attempts	(int | None):							Maximum number of attempts (None for infinite retries)
		delay			(float):								Initial delay in seconds between retries (default: 1.0)
		backoff			(float):								Multiplier for delay after each retry (default: 1.0 for constant delay)

	Returns:
		Callable[..., Any]: Decorator that retries the function on specified exceptions

	Examples:
		>>> import os
		>>> @retry(exceptions=PermissionError, max_attempts=3, delay=0.1)
		... def write_file():
		...     with open("test.txt", "w") as f:
		...         f.write("test")

		>>> @retry(exceptions=(OSError, IOError), delay=0.5, backoff=2.0)
		... def network_call():
		...     pass

		>>> @retry(max_attempts=5, delay=1.0)
		... def might_fail():
		...     pass
	"""
	# Normalize exceptions to tuple
	if not isinstance(exceptions, tuple):
		exceptions = (exceptions,)

	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			attempt: int = 0
			current_delay: float = delay

			while True:
				attempt += 1
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					# Check if we should retry or give up
					if max_attempts != 1 and attempt >= max_attempts:
						raise e

					# Log retry attempt
					warning(f"{type(e).__name__} encountered while running {_get_func_name(func)}, retrying ({attempt + 1}/{max_attempts}): {e}")

					# Wait before next attempt
					time.sleep(current_delay)
					current_delay *= backoff

		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.retry", func)
		return wrapper

	# Handle both @retry and @retry(exceptions=..., max_attempts=..., delay=...)
	if func is None:
		return decorator
	return decorator(func)

# Decorator that marks a function as abstract
def abstract(
	func: Callable[..., Any] | None = None,
	*,
	error_log: LogLevels = LogLevels.RAISE_EXCEPTION
) -> Callable[..., Any]:
	""" Decorator that marks a function as abstract.

	Contrary to the abstractmethod decorator from the abc module that raises a TypeError
	when you try to instantiate a class that has abstract methods, this decorator raises
	a NotImplementedError ONLY when the decorated function is called, indicating that the function
	must be implemented by a subclass.

	Args:
		func                (Callable[..., Any] | None): The function to mark as abstract
		error_log           (LogLevels):                 Log level for the error handling
			LogLevels.NONE:              None
			LogLevels.WARNING:           Show as warning
			LogLevels.WARNING_TRACEBACK: Show as warning with traceback
			LogLevels.ERROR_TRACEBACK:   Show as error with traceback
			LogLevels.RAISE_EXCEPTION:   Raise exception

	Returns:
		Callable[..., Any]: Decorator that raises NotImplementedError when called

	Examples:
		>>> class Base:
		...     @abstract
		...     def method(self):
		...         pass
		>>> Base().method()
		Traceback (most recent call last):
			...
		NotImplementedError: Function 'method' is abstract and must be implemented by a subclass
	"""
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		message: str = f"Function '{_get_func_name(func)}' is abstract and must be implemented by a subclass"
		if not func.__doc__:
			func.__doc__ = message

		@wraps(func)
		@handle_error(exceptions=NotImplementedError, error_log=error_log)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			raise NotImplementedError(message)
		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.abstract", func)
		return wrapper

	# Handle both @abstract and @abstract(error_log=...)
	if func is None:
		return decorator
	return decorator(func)

# Decorator that marks a function as deprecated
def deprecated(
	func: Callable[..., Any] | None = None,
	*,
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING
) -> Callable[..., Any]:
	""" Decorator that marks a function as deprecated.

	Args:
		func        (Callable[..., Any] | None): Function to mark as deprecated
		message     (str):                       Additional message to display with the deprecation warning
		error_log   (LogLevels):                 Log level for the deprecation warning
			LogLevels.NONE:              None
			LogLevels.WARNING:           Show as warning
			LogLevels.WARNING_TRACEBACK: Show as warning with traceback
			LogLevels.ERROR_TRACEBACK:   Show as error with traceback
			LogLevels.RAISE_EXCEPTION:   Raise exception
	Returns:
		Callable[..., Any]: Decorator that marks a function as deprecated

	Examples:
		>>> @deprecated
		... def old_function():
		...     pass

		>>> @deprecated(message="Use 'new_function()' instead", error_log=LogLevels.WARNING)
		... def another_old_function():
		...     pass
	"""
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Build deprecation message
			msg: str = f"Function '{_get_func_name(func)}()' is deprecated"
			if message:
				msg += f". {message}"

			# Handle deprecation warning based on log level
			if error_log == LogLevels.WARNING:
				warning(msg)
			elif error_log == LogLevels.WARNING_TRACEBACK:
				warning(f"{msg}\n{format_exc()}")
			elif error_log == LogLevels.ERROR_TRACEBACK:
				error(f"{msg}\n{format_exc()}", exit=True)
			elif error_log == LogLevels.RAISE_EXCEPTION:
				raise DeprecationWarning(msg)

			# Call the original function
			return func(*args, **kwargs)
		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.deprecated", func)
		return wrapper

	# Handle both @deprecated and @deprecated(message=..., error_log=...)
	if func is None:
		return decorator
	return decorator(func)

# Decorator that make a function silent (disable stdout)
def silent(
	func: Callable[..., Any] | None = None,
	*,
	mute_stderr: bool = False
) -> Callable[..., Any]:
	""" Decorator that makes a function silent (disable stdout, and stderr if specified).

	Alternative to stouputils.ctx.Muffle.

	Args:
		func			(Callable[..., Any] | None):	Function to make silent
		mute_stderr		(bool):							Whether to mute stderr or not

	Examples:
		>>> @silent
		... def test():
		...     print("Hello, world!")
		>>> test()

		>>> @silent(mute_stderr=True)
		... def test2():
		...     print("Hello, world!")
		>>> test2()

		>>> silent(print)("Hello, world!")
	"""
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Use Muffle context manager to silence output
			with Muffle(mute_stderr=mute_stderr):
				return func(*args, **kwargs)
		wrapper.__name__ = _get_wrapper_name("stouputils.decorators.silent", func)
		return wrapper

	# Handle both @silent and @silent(mute_stderr=...)
	if func is None:
		return decorator
	return decorator(func)



# "Private" functions
def _get_func_name(func: Callable[..., Any]) -> str:
	""" Get the name of a function, returns "<unknown>" if the name cannot be retrieved. """
	try:
		return func.__name__
	except AttributeError:
		return "<unknown>"

def _get_wrapper_name(decorator_name: str, func: Callable[..., Any]) -> str:
	""" Get a descriptive name for a wrapper function.

	Args:
		decorator_name	(str):					Name of the decorator
		func			(Callable[..., Any]):	Function being decorated
	Returns:
		str: Combined name for the wrapper function (e.g., "stouputils.decorators.handle_error@function_name")
	"""
	func_name: str = _get_func_name(func)

	# Remove "stouputils.decorators.*" prefix if present
	if func_name.startswith("stouputils.decorators."):
		func_name = ".".join(func_name.split(".")[3:])

	return f"{decorator_name}@{func_name}"

