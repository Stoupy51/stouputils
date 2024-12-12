"""
This module provides decorators for various purposes:
- silent(): Make a function silent (disable stdout, and stderr if specified)
- measure_time(): Measure the execution time of a function and print it with the given print function
- handle_error(): Handle an error with different log levels
"""

# Imports
import os
import sys
import time
from traceback import format_exc
from typing import Callable, Any
from functools import wraps
from .print import *


# Decorator that make a function silent (disable stdout)
def silent(
	func: Callable[..., Any],
	mute_stderr: bool = False
) -> Callable[..., Any]:
	""" Decorator that make a function silent (disable stdout, and stderr if specified)\n
	Alternative to stouputils.ctx.Muffle

	Args:
		func			(Callable):		Function to make silent
		mute_stderr		(bool):			Whether to mute stderr or not
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
	""" Decorator that will measure the execution time of a function and print it with the given print function\n
	Args:
		print_func		(Callable):	Function to use to print the execution time (e.g. debug, info, warning, error, etc.)
		message			(str):		Message to display with the execution time (e.g. "Execution time of Something"), defaults to "Execution time of {func.__name__}"
		perf_counter	(bool):		Whether to use time.perf_counter_ns or time.time_ns
	Returns:
		Callable:	Decorator to measure the time of the function.
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
class LOG_LEVELS:
	""" Log level for the errors in the decorator handle_error()
	Attributes:
		NONE: Do nothing
		WARNING: Show as warning
		WARNING_TRACEBACK: Show as warning with traceback
		ERROR_TRACEBACK: Show as error with traceback
		RAISE_EXCEPTION: Raise exception
	"""
	NONE: int = 0
	""" Do nothing """
	WARNING: int = 1
	""" Show as warning """
	WARNING_TRACEBACK: int = 2
	""" Show as warning with traceback """
	ERROR_TRACEBACK: int = 3
	""" Show as error with traceback """
	RAISE_EXCEPTION: int = 4
	""" Raise exception """

def handle_error(
	exceptions: tuple[type[Exception], ...] | type[Exception] = (Exception,),
	message: str = "",
	error_log: int = LOG_LEVELS.ERROR_TRACEBACK
) -> Callable[..., Any]:
	""" Decorator that handle an error with different log levels.\n
	Args:
		exceptions		(tuple[type[Exception]], ...):	Exceptions to handle
		message			(str):							Message to display with the error. (e.g. "Error during something")
		error_log		(int):							Log level for the errors
			LOG_LEVELS.NONE:				None
			LOG_LEVELS.WARNING:				Show as warning
			LOG_LEVELS.WARNING_TRACEBACK:	Show as warning with traceback
			LOG_LEVELS.ERROR_TRACEBACK:		Show as error with traceback
			LOG_LEVELS.RAISE_EXCEPTION:		Raise exception (as if the decorator didn't exist)
	"""
	# Convert the exceptions to a tuple if not already
	if not isinstance(exceptions, tuple):
		exceptions = (exceptions,)

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
				if error_log == LOG_LEVELS.WARNING:
					warning(f"{msg}Error during {func.__name__}: ({type(e).__name__}) {e}")
				elif error_log == LOG_LEVELS.WARNING_TRACEBACK:
					warning(f"{msg}Error during {func.__name__}:\n{format_exc()}")
				elif error_log == LOG_LEVELS.ERROR_TRACEBACK:
					error(f"{msg}Error during {func.__name__}:\n{format_exc()}", exit=True)
				elif error_log >= LOG_LEVELS.RAISE_EXCEPTION:
					raise e
		return wrapper
	return decorator

