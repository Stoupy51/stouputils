
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import signal
import threading
from collections.abc import Callable
from typing import Any, overload

from ..typing import JsonList
from .common import get_function_name, get_wrapper_name, safe_wraps, set_wrapper_name


# Decorator that raises an exception if the function runs too long
@overload
def timeout[T](
	func: Callable[..., T],
	*,
	seconds: float = 60.0,
	message: str = ""
) -> Callable[..., T]: ...

@overload
def timeout[T](
	func: None = None,
	*,
	seconds: float = 60.0,
	message: str = ""
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def timeout[T](
	func: Callable[..., T] | None = None,
	*,
	seconds: float = 60.0,
	message: str = ""
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that raises a TimeoutError if the function runs longer than the specified timeout.

	Note: This decorator uses SIGALRM on Unix systems, which only works in the main thread.
	On Windows or in non-main threads, it will fall back to a polling-based approach.

	Args:
		func:    Function to apply timeout to
		seconds: Timeout duration in seconds (default: 60.0)
		message: Custom timeout message (default: "Function '{func_name}' timed out after {seconds} seconds")

	Raises:
		:py:exc:`TimeoutError`: If the function execution exceeds the timeout duration
	>>> import time
	>>> @timeout(seconds=2.0)
	... def slow_function():
	...     time.sleep(5)
	>>> slow_function()  # Raises TimeoutError after 2 seconds
	Traceback (most recent call last):
		...
	TimeoutError: Function 'slow_function()' timed out after 2.0 seconds

	>>> @timeout(seconds=1.0, message="Custom timeout message")
	... def another_slow_function():
	...     time.sleep(3)
	>>> another_slow_function()  # Raises TimeoutError after 1 second
	Traceback (most recent call last):
		...
	TimeoutError: Custom timeout message
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@safe_wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			msg: str = message if message else f"Function '{get_function_name(func)}()' timed out after {seconds} seconds"

			# SIGALRM exists on Unix only, and only the main thread receives it
			if hasattr(signal, "SIGALRM") and threading.current_thread() is threading.main_thread():
				return run_with_alarm(func, args, kwargs, seconds, msg)
			return run_in_thread(func, args, kwargs, seconds, msg)

		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.timeout", func))
		return wrapper

	# Handle both @timeout and @timeout(seconds=..., message=...)
	if func is None:
		return decorator
	return decorator(func)


def run_with_alarm[T](func: Callable[..., T], args: tuple[Any, ...], kwargs: dict[str, Any], seconds: float, message: str) -> T:
	""" Call ``func`` under a SIGALRM timer, which interrupts it wherever it is, restoring the previous handler afterwards.

	Raises:
		TimeoutError: If the call outlasts ``seconds``, carrying ``message``.
	"""
	def timeout_handler(signum: int, frame: Any) -> None:
		raise TimeoutError(message)

	old_handler = signal.signal(signal.SIGALRM, timeout_handler)
	signal.setitimer(signal.ITIMER_REAL, seconds)
	try:
		return func(*args, **kwargs)
	finally:
		signal.setitimer(signal.ITIMER_REAL, 0)
		signal.signal(signal.SIGALRM, old_handler)


def run_in_thread[T](func: Callable[..., T], args: tuple[Any, ...], kwargs: dict[str, Any], seconds: float, message: str) -> T:
	""" Call ``func`` in a daemon thread and stop waiting after ``seconds``, the thread itself running on until it returns.

	Raises:
		TimeoutError: If the call outlasts ``seconds``, carrying ``message``.
	"""
	result_container: JsonList = []
	exception_container: list[BaseException] = []

	def target() -> None:
		try:
			result_container.append(func(*args, **kwargs))
		except BaseException as e:
			exception_container.append(e)

	thread = threading.Thread(target=target, daemon=True)
	thread.start()
	thread.join(timeout=seconds)
	if thread.is_alive():
		raise TimeoutError(message)
	if exception_container:
		raise exception_container[0]
	return result_container[0]

