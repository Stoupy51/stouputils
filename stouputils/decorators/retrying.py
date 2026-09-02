
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import time
from collections.abc import Callable, Iterable
from typing import Any, overload

from ..print.message import warning
from .common import get_function_name, get_wrapper_name, safe_wraps, set_wrapper_name


# Decorator that retries a function when specific exceptions are raised
@overload
def retry[T](
	func: Callable[..., T],
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	max_attempts: int | Iterable[float] | None = 10,
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
	max_attempts: int | Iterable[float] | None = 10,
	delay: float = 1.0,
	backoff: float = 1.0,
	message: str = "",
	on_each_failure: Callable[[BaseException, int], Any] | None = None
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def retry[T](
	func: Callable[..., T] | None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	max_attempts: int | Iterable[float] | None = 10,
	delay: float = 1.0,
	backoff: float = 1.0,
	message: str = "",
	on_each_failure: Callable[[BaseException, int], Any] | None = None
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that retries a function when specific exceptions are raised.

	Args:
		func:            Function to retry
		exceptions:      Exceptions to catch and retry on
		max_attempts:    Maximum number of attempts, None for infinite retries.
			An iterable of seconds gives one delay per attempt instead: its length is the attempt count, and delay/backoff are ignored.
		delay:           Initial delay in seconds between retries (default: 1.0)
		backoff:         Multiplier for delay after each retry (default: 1.0 for constant delay)
		message:         Custom message to display before ", retrying" (default: "{ExceptionName} encountered while running {func_name}")
		on_each_failure: Optional callback function to call on each failure, receives the exception and the attempt number as arguments
	Returns:
		Decorator that retries the function on specified exceptions

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

	>>> # Use a lambda to record attempts on each failure
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

	>>> # An iterable of delays sets both the waits and the attempt count
	>>> attempts = []
	>>> @retry(max_attempts=(0.0, 0.0, 0.0, 0.0), on_each_failure=lambda e, a: attempts.append(a))
	... def flaky():
	...     raise ValueError("nope")
	>>> try:
	...     flaky()
	... except ValueError:
	...     pass
	>>> attempts
	[1, 2, 3, 4]
	"""
	# Normalize exceptions to tuple
	if not isinstance(exceptions, tuple):
		exceptions = (exceptions,)

	# An iterable of max_attempts carries one delay per attempt, its length being the attempt count
	delays: tuple[float, ...] | None = None
	attempt_limit: int | None = None
	if isinstance(max_attempts, int | None):
		attempt_limit = max_attempts
	else:
		delays = tuple(max_attempts)
		attempt_limit = len(delays)

	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@safe_wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> T:
			attempt: int = 0

			while True:
				attempt += 1
				try:
					return func(*args, **kwargs)
				except exceptions as e:
					# Call on_each_failure callback if provided
					if on_each_failure is not None:
						on_each_failure(e, attempt)

					# Check if we should retry or give up
					if attempt_limit is not None and attempt >= attempt_limit:
						raise e

					# Log retry attempt
					current_delay: float = delays[attempt - 1] if delays is not None else delay * backoff ** (attempt - 1)
					attempts_display: str = f"{attempt + 1}/{attempt_limit}" if attempt_limit is not None else f"{attempt + 1}/∞"
					if message:
						warning(f"{message}, retrying in {current_delay}s ({attempts_display}): {e}")
					else:
						warning(f"{type(e).__name__} encountered while running {get_function_name(func)}(), retrying in {current_delay}s ({attempts_display}): {e}")

					# Wait before next attempt
					time.sleep(current_delay)

		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.retry", func))
		return wrapper

	# Handle both @retry and @retry(exceptions=..., max_attempts=..., delay=...)
	if func is None:
		return decorator
	return decorator(func)

