
# Imports
from collections.abc import Callable
from functools import wraps
from typing import Any, overload

from ..typing import JsonList
from .common import get_function_name, get_wrapper_name, set_wrapper_name


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
		func		(Callable[..., T] | None):	Function to apply timeout to
		seconds		(float):					Timeout duration in seconds (default: 60.0)
		message		(str):						Custom timeout message (default: "Function '{func_name}' timed out after {seconds} seconds")

	Raises:
		:py:exc:`TimeoutError`: If the function execution exceeds the timeout duration

	Examples:
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
		# Check if we can use signal-based timeout (Unix only)
		import os
		use_signal: bool = os.name != "nt"  # Not Windows

		if use_signal:
			try:
				import signal
				# Verify SIGALRM is available
				use_signal = hasattr(signal, 'SIGALRM')
			except ImportError:
				use_signal = False

		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Build timeout message
			msg: str = message if message else f"Function '{get_function_name(func)}()' timed out after {seconds} seconds"

			# Use signal-based timeout on Unix (main thread only)
			if use_signal:
				import signal
				import threading

				# Signal only works in main thread
				if threading.current_thread() is threading.main_thread():
					def timeout_handler(signum: int, frame: Any) -> None:
						raise TimeoutError(msg)

					# Set the signal handler and alarm
					old_handler = signal.signal(signal.SIGALRM, timeout_handler) # type: ignore
					signal.setitimer(signal.ITIMER_REAL, seconds) # type: ignore

					try:
						result = func(*args, **kwargs)
					finally:
						# Cancel the alarm and restore the old handler
						signal.setitimer(signal.ITIMER_REAL, 0) # type: ignore
						signal.signal(signal.SIGALRM, old_handler) # type: ignore

					return result

			# Fall back to polling-based timeout (Windows or non-main thread)
			import threading

			result_container: JsonList = []
			exception_container: list[BaseException] = []

			def target() -> None:
				try:
					result_container.append(func(*args, **kwargs))
				except BaseException as e_2:
					exception_container.append(e_2)

			thread = threading.Thread(target=target, daemon=True)
			thread.start()
			thread.join(timeout=seconds)

			if thread.is_alive():
				# Thread is still running, timeout occurred
				raise TimeoutError(msg)

			# Check if an exception was raised in the thread
			if exception_container:
				raise exception_container[0]

			# Return the result if available
			if result_container:
				return result_container[0]

		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.timeout", func))
		return wrapper

	# Handle both @timeout and @timeout(seconds=..., message=...)
	if func is None:
		return decorator
	return decorator(func)

