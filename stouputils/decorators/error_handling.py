
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import time
from collections.abc import Callable
from enum import Enum
from traceback import format_exc
from typing import Any, overload

from ..config import StouputilsConfig as Cfg
from ..print.message import error, warning
from .common import get_function_name, get_wrapper_name, safe_wraps, set_wrapper_name


# Decorator that handle an error with different log levels
class LogLevels(Enum):
	""" Log level for the errors in the decorator handle_error """
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

@overload
def handle_error[T](
	func: Callable[..., T],
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0,
	callback: Callable[[BaseException], None] | None = None
) -> Callable[..., T]: ...

@overload
def handle_error[T](
	func: None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0,
	callback: Callable[[BaseException], None] | None = None
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def handle_error[T](
	func: Callable[..., T] | None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0,
	callback: Callable[[BaseException], None] | None = None
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that handle an error with different log levels.

	Args:
		func:       Function to decorate
		exceptions: Exceptions to handle
		message:    Message to display with the error (e.g. "Error during something")
		error_log:  Log level for the errors

			- :attr:`LogLevels.NONE` - None
			- :attr:`LogLevels.WARNING` - Show as warning
			- :attr:`LogLevels.WARNING_TRACEBACK` - Show as warning with traceback
			- :attr:`LogLevels.ERROR_TRACEBACK` - Show as error with traceback
			- :attr:`LogLevels.RAISE_EXCEPTION` - Raise exception

		sleep_time: Seconds to sleep after the error, 0.0 not to sleep
		callback:   Called with the exception, None for no callback
	>>> @handle_error
	... def might_fail():
	...     raise ValueError("Let's fail")

	>>> @handle_error(error_log=LogLevels.WARNING)
	... def test():
	...     raise ValueError("Let's fail")
	>>> # test()	# [WARNING HH:MM:SS] Error during test: (ValueError) Let's fail
	"""
	# Update error_log if needed
	if Cfg.FORCE_RAISE_EXCEPTION:
		error_log = LogLevels.RAISE_EXCEPTION

	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		prefix: str = f"{message}, " if message else ""

		@safe_wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			try:
				return func(*args, **kwargs)
			except exceptions as e:
				if error_log == LogLevels.RAISE_EXCEPTION:
					raise
				report_error(error_log, f"{prefix}Error during {get_function_name(func)}()", e, sleep_time, callback)
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.handle_error", func))
		return wrapper

	# Handle both @handle_error and @handle_error(exceptions=..., message=..., error_log=...)
	if func is None:
		return decorator
	return decorator(func)


def report_error(
	error_log: LogLevels, heading: str, exception: BaseException, sleep_time: float, callback: Callable[[BaseException], None] | None
) -> None:
	""" React to an exception :func:`handle_error` caught at a level that does not raise, from inside its ``except`` block.

	Args:
		heading:    Opening of the message, naming where the exception happened.
		sleep_time: Seconds to sleep afterwards, skipped at ``ERROR_TRACEBACK`` since its prompt already waited.
	"""
	if error_log == LogLevels.WARNING:
		warning(f"{heading}: ({type(exception).__name__}) {exception}")
	elif error_log == LogLevels.WARNING_TRACEBACK:
		warning(f"{heading}:\n{format_exc()}")
	elif error_log == LogLevels.ERROR_TRACEBACK:
		error(f"{heading}:\n{format_exc()}", exit=True)
	if sleep_time > 0.0 and error_log != LogLevels.ERROR_TRACEBACK:
		time.sleep(sleep_time)
	if callback is not None:
		callback(exception)

