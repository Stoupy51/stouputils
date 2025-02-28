"""
This module provides decorators for various purposes:

- silent(): Make a function silent (disable stdout, and stderr if specified) (alternative to stouputils.ctx.Muffle)
- measure_time(): Measure the execution time of a function and print it with the given print function
- handle_error(): Handle an error with different log levels
- simple_cache(): Easy cache function with parameter caching method
- deprecated(): Mark a function as deprecated

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_1.gif
  :alt: stouputils decorators examples

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/decorators_module_2.gif
  :alt: stouputils decorators examples
"""

# Imports
import os
import sys
import time
from enum import Enum
from pickle import dumps as pickle_dumps
from traceback import format_exc
from typing import Callable, Literal, Any
from functools import wraps
from .print import debug, warning, error


# Decorator that make a function silent (disable stdout)
def silent(
	func: Callable[..., Any],
	mute_stderr: bool = False
) -> Callable[..., Any]:
	""" Decorator that makes a function silent (disable stdout, and stderr if specified).

	Alternative to stouputils.ctx.Muffle.

	Args:
		func			(Callable[..., Any]):	Function to make silent
		mute_stderr		(bool):					Whether to mute stderr or not

	Examples:
		>>> @silent
		... def test():
		...     print("Hello, world!")
		>>> test()

		>>> silent(print)("Hello, world!")
	"""
	@wraps(func)
	def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:

		# Disable stdout and stderr
		_original_stdout: Any = sys.stdout
		_original_stderr: Any = None
		sys.stdout = open(os.devnull, "w", encoding="utf-8")
		if mute_stderr:
			_original_stderr = sys.stderr
			sys.stderr = open(os.devnull, "w", encoding="utf-8")

		# Call the function
		result: Any = func(*args, **kwargs)

		# Re-Enable stdout and stderr
		sys.stdout.close()
		sys.stdout = _original_stdout
		if mute_stderr:
			sys.stderr.close()
			sys.stderr = _original_stderr
		return result
	return wrapper



# Execution time decorator
def measure_time(
	print_func: Callable[..., None] = debug,
	message: str = "",
	perf_counter: bool = True
) -> Callable[..., Any]:
	""" Decorator that will measure the execution time of a function and print it with the given print function

	Args:
		print_func		(Callable):	Function to use to print the execution time (e.g. debug, info, warning, error, etc.)
		message			(str):		Message to display with the execution time (e.g. "Execution time of Something"), defaults to "Execution time of {func.__name__}"
		perf_counter	(bool):		Whether to use time.perf_counter_ns or time.time_ns
	Returns:
		Callable:	Decorator to measure the time of the function.
	
	Examples:
		.. code-block:: python

			> @measure_time(info)
			> def test():
			>     pass
			> test()  # [INFO HH:MM:SS] Execution time of test: 0.000ms (400ns)
	"""
	ns: Callable[[], int] = time.perf_counter_ns if perf_counter else time.time_ns
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:

		# Set the message if not specified
		nonlocal message
		if not message:
			message = f"Execution time of {func.__name__}"

		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:

			# Measure the execution time (nanoseconds and seconds)
			start_ns: int = ns()
			result = func(*args, **kwargs)
			total_ns: int = ns() - start_ns
			total_ms: float = total_ns / 1_000_000
			total_s: float = total_ns / 1_000_000_000

			# Print the execution time (nanoseconds if less than 0.3s, seconds otherwise)
			if total_ms < 300:
				print_func(f"{message}: {total_ms:.3f}ms ({total_ns}ns)")
			elif total_s < 60:
				print_func(f"{message}: {(total_s):.5f}s")
			else:
				minutes: int = int(total_s) // 60
				seconds: int = int(total_s) % 60
				if minutes < 60:
					print_func(f"{message}: {minutes}m {seconds}s")
				else:
					hours: int = minutes // 60
					minutes: int = minutes % 60
					if hours < 24:
						print_func(f"{message}: {hours}h {minutes}m {seconds}s")
					else:
						days: int = hours // 24
						hours: int = hours % 24
						print_func(f"{message}: {days}d {hours}h {minutes}m {seconds}s")
			return result
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
""" If true, the error_log parameter will be set to RAISE_EXCEPTION for every next handle_error calls, useful for doctests """

def handle_error(
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.ERROR_TRACEBACK
) -> Callable[..., Any]:
	""" Decorator that handle an error with different log levels.

	Args:
		exceptions		(tuple[type[BaseException]], ...):	Exceptions to handle
		message			(str):								Message to display with the error. (e.g. "Error during something")
		error_log		(LogLevels):						Log level for the errors
			LogLevels.NONE:					None
			LogLevels.WARNING:				Show as warning
			LogLevels.WARNING_TRACEBACK:	Show as warning with traceback
			LogLevels.ERROR_TRACEBACK:		Show as error with traceback
			LogLevels.RAISE_EXCEPTION:		Raise exception (as if the decorator didn't exist)
	
	Examples:
		.. code-block:: python

			> @handle_error(error_log=LogLevels.WARNING)
			> def test():
			>     raise ValueError("Let's fail")
			> test()	# [WARNING HH:MM:SS] Error during test: (ValueError) Let's fail
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
					warning(f"{msg}Error during {func.__name__}: ({type(e).__name__}) {e}")
				elif error_log == LogLevels.WARNING_TRACEBACK:
					warning(f"{msg}Error during {func.__name__}:\n{format_exc()}")
				elif error_log == LogLevels.ERROR_TRACEBACK:
					error(f"{msg}Error during {func.__name__}:\n{format_exc()}", exit=True)
				elif error_log == LogLevels.RAISE_EXCEPTION:
					raise e
		return wrapper
	return decorator



# Easy cache function with parameter caching method
def simple_cache(method: Literal["str", "pickle"] = "str") -> Callable[..., Callable[..., Any]]:
	""" Decorator that caches the result of a function based on its arguments.

	The str method is often faster than the pickle method (by a little).

	Args:
		method (Literal["str", "pickle"]): The method to use for caching.
	Returns:
		Callable[..., Callable[..., Any]]: A decorator that caches the result of a function.
	Examples:
		>>> @simple_cache(method="str")
		... def test(a: int, b: int) -> int:
		...     return a + b
		>>> test(1, 2)	# 3
		3
		>>> test(1, 2)	# 3
		3
		>>> test(3, 4)	# 7
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
		return wrapper

	# Return the decorator
	return decorator


def deprecated(
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING
) -> Callable[..., Any]:
	""" Decorator that marks a function as deprecated.

	Args:
		message     (str):               Additional message to display with the deprecation warning
		error_log   (LogLevels):         Log level for the deprecation warning
			LogLevels.NONE:              None 
			LogLevels.WARNING:           Show as warning
			LogLevels.WARNING_TRACEBACK: Show as warning with traceback
			LogLevels.ERROR_TRACEBACK:   Show as error with traceback
			LogLevels.RAISE_EXCEPTION:   Raise exception
	Returns:
		Callable[..., Any]: Decorator that marks a function as deprecated
	
	Examples:
		.. code-block:: python

			> @deprecated(message="Use 'this_function()' instead", error_log=LogLevels.WARNING)
			> def test():
			>     pass
			> test()	# [WARNING HH:MM:SS] Function 'test()' is deprecated. Use 'this_function()' instead
	"""
	def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Build deprecation message
			msg: str = f"Function '{func.__name__}()' is deprecated"
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
		return wrapper
	return decorator

