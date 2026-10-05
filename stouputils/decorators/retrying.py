
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, overload

from ..print.message import warning
from .common import get_function_name, get_wrapper_name, safe_wraps, set_wrapper_name


# Classes
@dataclass(frozen=True)
class RetryPolicy:
	""" Helper class for how :func:`retry` calls a function again: on which exceptions, how many times, and after which waits. """
	exceptions: tuple[type[BaseException], ...]
	""" Exceptions to catch and retry on. """
	attempt_limit: int | None
	""" Attempts allowed in total, None for no limit. """
	delays: tuple[float, ...] | None
	""" Seconds to wait after each failed attempt, replacing ``delay`` and ``backoff`` when given. """
	delay: float
	""" Initial delay in seconds between retries (default: 1.0). """
	backoff: float
	""" Multiplier for delay after each retry (default: 1.0 for constant delay). """
	message: str
	""" Custom message to display before ", retrying" (default: "{ExceptionName} encountered while running {func_name}"). """
	on_each_failure: Callable[[BaseException, int], Any] | None
	""" Optional callback function to call on each failure, receives the exception and the attempt number as arguments. """

	def call[T](self, func: Callable[..., T], args: tuple[Any, ...], kwargs: dict[str, Any]) -> T:
		""" Call ``func`` until it returns, raising its last exception once the attempts run out. """
		attempt: int = 0
		while True:
			attempt += 1
			try:
				return func(*args, **kwargs)
			except self.exceptions as e:
				if self.on_each_failure is not None:
					self.on_each_failure(e, attempt)
				if self.attempt_limit is not None and attempt >= self.attempt_limit:
					raise
				wait: float = self.wait_after(attempt)
				warning(retry_warning(e, func, self.message, wait, attempt, self.attempt_limit))
				time.sleep(wait)

	def wait_after(self, attempt: int) -> float:
		""" Seconds to wait after the given failed attempt, counted from 1. """
		return self.delays[attempt - 1] if self.delays is not None else self.delay * self.backoff ** (attempt - 1)


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
		message:         Custom message to display before ", retrying"
			(default: "{ExceptionName} encountered while running {func_name}")
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
	# An iterable of max_attempts carries one delay per attempt, its length being the attempt count
	delays: tuple[float, ...] | None = None
	attempt_limit: int | None = None
	if isinstance(max_attempts, int | None):
		attempt_limit = max_attempts
	else:
		delays = tuple(max_attempts)
		attempt_limit = len(delays)
	policy: RetryPolicy = RetryPolicy(
		exceptions=exceptions if isinstance(exceptions, tuple) else (exceptions,),
		attempt_limit=attempt_limit,
		delays=delays,
		delay=delay,
		backoff=backoff,
		message=message,
		on_each_failure=on_each_failure,
	)

	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@safe_wraps(func)
		def wrapper(*args: Any, **kwargs: Any) -> T:
			return policy.call(func, args, kwargs)

		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.retry", func))
		return wrapper

	# Handle both @retry and @retry(exceptions=..., max_attempts=..., delay=...)
	if func is None:
		return decorator
	return decorator(func)


def retry_warning(
	error: BaseException, func: Callable[..., Any], message: str, delay: float, attempt: int, attempt_limit: int | None
) -> str:
	""" The warning :func:`retry` prints before waiting for the next attempt.

	Args:
		message:       Text opening the warning, the error and the function name when empty.
		attempt:       Number of the attempt that just failed, from 1.
		attempt_limit: Attempts allowed in total, None for no limit.

	>>> retry_warning(OSError("busy"), print, "", 0.5, 1, None)
	'OSError encountered while running print(), retrying in 0.5s (2/∞): busy'
	>>> retry_warning(OSError("busy"), print, "Lock taken", 2.0, 2, 3)
	'Lock taken, retrying in 2.0s (3/3): busy'
	"""
	prefix: str = message or f"{type(error).__name__} encountered while running {get_function_name(func)}()"
	return f"{prefix}, retrying in {delay}s ({attempt + 1}/{'∞' if attempt_limit is None else attempt_limit}): {error}"

