
# Imports
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, overload

from ..print.message import warning
from .common import get_function_name, get_wrapper_name, set_wrapper_name


# Decorator that retries a function when specific exceptions are raised
@overload
def retry[T](
	func: Callable[..., T],
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	max_attempts: int | None = 10,
	delay: float = 1.0,
	backoff: float = 1.0,
	message: str = "",
	on_each_failure: Callable[[BaseException, int], Any] | None = None
) -> Callable[..., T]: ...

@overload
def retry[T](
	func: None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	max_attempts: int | None = 10,
	delay: float = 1.0,
	backoff: float = 1.0,
	message: str = "",
	on_each_failure: Callable[[BaseException, int], Any] | None = None
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def retry[T](
	func: Callable[..., T] | None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	max_attempts: int | None = 10,
	delay: float = 1.0,
	backoff: float = 1.0,
	message: str = "",
	on_each_failure: Callable[[BaseException, int], Any] | None = None
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that retries a function when specific exceptions are raised.

	Args:
		func			(Callable[..., T] | None):		Function to retry
		exceptions		(tuple[type[BaseException], ...]):	Exceptions to catch and retry on
		max_attempts	(int | None):						Maximum number of attempts (None for infinite retries)
		delay			(float):							Initial delay in seconds between retries (default: 1.0)
		backoff			(float):							Multiplier for delay after each retry (default: 1.0 for constant delay)
		message			(str):								Custom message to display before ", retrying" (default: "{ExceptionName} encountered while running {func_name}")
		on_each_failure	(Callable[[BaseException, int], Any] | None): Optional callback function to call on each failure, receives the exception and the attempt number as arguments
	Returns:
		Callable[..., T]: Decorator that retries the function on specified exceptions

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

		>>> # Example: use a lambda to record attempts on each failure
		>>> calls = []
		>>> @retry(max_attempts=3, delay=0.0, on_each_failure=lambda e, a: calls.append((e, a)))
		... def will_fail():
		...     raise RuntimeError("nope")
		>>> try:
		...     will_fail()
		... except RuntimeError:
		...     pass
		>>> calls
		[(RuntimeError('nope'), 1), (RuntimeError('nope'), 2), (RuntimeError('nope'), 3)]
	"""
	# Normalize exceptions to tuple
	if not isinstance(exceptions, tuple):
		exceptions = (exceptions,)

	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> T:
			attempt: int = 0
			current_delay: float = delay

			while True:
				attempt += 1
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					# Call on_each_failure callback if provided
					if on_each_failure is not None:
						on_each_failure(e, attempt)

					# Check if we should retry or give up
					if max_attempts is not None and attempt >= max_attempts:
						raise e

					# Log retry attempt
					attempts_display: str = f"{attempt + 1}/{max_attempts}" if max_attempts is not None else f"{attempt + 1}/∞"
					if message:
						warning(f"{message}, retrying in {current_delay}s ({attempts_display}): {e}")
					else:
						warning(f"{type(e).__name__} encountered while running {get_function_name(func)}(), retrying in {current_delay}s ({attempts_display}): {e}")

					# Wait before next attempt
					time.sleep(current_delay)
					current_delay *= backoff

		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.retry", func))
		return wrapper

	# Handle both @retry and @retry(exceptions=..., max_attempts=..., delay=...)
	if func is None:
		return decorator
	return decorator(func)

