
# Imports
from collections.abc import Callable, Generator
from functools import wraps
from typing import Any, Literal, overload

from ..ctx import MeasureTime
from ..print.message import progress
from .common import get_function_name, get_wrapper_name, set_wrapper_name


# Execution time decorator
# Regular function overloads (is_generator=False)
@overload
def measure_time[T](
	func: Callable[..., T],
	*,
	printer: Callable[..., None] = progress,
	message: str = "",
	perf_counter: bool = True,
	is_generator: Literal[False] = False
) -> Callable[..., T]: ...

@overload
def measure_time[T](
	func: None = None,
	*,
	printer: Callable[..., None] = progress,
	message: str = "",
	perf_counter: bool = True,
	is_generator: Literal[False] = False
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

# Generator function overloads (is_generator=True)
@overload
def measure_time[T](
	func: Callable[..., Generator[T, None, None]],
	*,
	printer: Callable[..., None] = progress,
	message: str = "",
	perf_counter: bool = True,
	is_generator: Literal[True]
) -> Callable[..., Generator[T, None, None]]: ...

@overload
def measure_time[T](
	func: None,
	*,
	printer: Callable[..., None] = progress,
	message: str = "",
	perf_counter: bool = True,
	is_generator: Literal[True]
) -> Callable[[Callable[..., Generator[T, None, None]]], Callable[..., Generator[T, None, None]]]: ...

def measure_time[T](
	func: Callable[..., T] | Callable[..., Generator[T, None, None]] | None = None,
	*,
	printer: Callable[..., None] = progress,
	message: str = "",
	perf_counter: bool = True,
	is_generator: bool = False
) -> (
	Callable[..., T]
	| Callable[..., Generator[T, None, None]]
	| Callable[[Callable[..., T]], Callable[..., T]]
	| Callable[[Callable[..., Generator[T, None, None]]], Callable[..., Generator[T, None, None]]]
):
	""" Decorator that will measure the execution time of a function and print it with the given print function

	Args:
		func			(Callable[..., Any] | None): Function to decorate
		printer			(Callable):	Function to use to print the execution time
			(e.g. :py:func:`~stouputils.print.debug`, :py:func:`~stouputils.print.info`, :py:func:`~stouputils.print.warning`, :py:func:`~stouputils.print.error`, etc.)
		message			(str):		Message to display with the execution time (e.g. "Execution time of Something"),
			defaults to "Execution time of {func.__name__}"
		perf_counter	(bool):		Whether to use time.perf_counter_ns or time.time_ns
			defaults to True (use time.perf_counter_ns)
		is_generator	(bool):		Whether the function is a generator or not (default: False)
			When True, the decorator will yield from the function instead of returning it.

	Returns:
		Callable: Decorator to measure the time of the function.

	Examples:
		.. code-block:: python

			> @measure_time(printer=info)
			> def test():
			>     pass
			> test()  # [INFO HH:MM:SS] Execution time of test: 0.000ms (400ns)
	"""
	def decorator(
		func: Callable[..., T] | Callable[..., Generator[T, None, None]]
	) -> Callable[..., T] | Callable[..., Generator[T, None, None]]:
		# Set the message if not specified, else use the provided one
		new_msg: str = message if message else f"Execution time of {get_function_name(func)}()"

		if is_generator:
			@wraps(func)
			def generator_wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Generator[T, None, None]:
				with MeasureTime(print_func=printer, message=new_msg, perf_counter=perf_counter):
					yield from func(*args, **kwargs)  # type: ignore
			set_wrapper_name(generator_wrapper, get_wrapper_name("stouputils.decorators.measure_time", func))
			return generator_wrapper
		else:
			@wraps(func)
			def regular_wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> T:
				with MeasureTime(print_func=printer, message=new_msg, perf_counter=perf_counter):
					return func(*args, **kwargs)  # type: ignore
			set_wrapper_name(regular_wrapper, get_wrapper_name("stouputils.decorators.measure_time", func))
			return regular_wrapper

	# Handle both @measure_time and @measure_time(printer=..., message=..., perf_counter=..., is_generator=...)
	if func is None:
		return decorator  # type: ignore
	return decorator(func)

