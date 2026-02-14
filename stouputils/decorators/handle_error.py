
# Imports
import time
from collections.abc import Callable
from enum import Enum
from functools import wraps
from traceback import format_exc
from typing import Any, overload

from ..config import StouputilsConfig as Cfg
from ..print.message import error, warning
from .common import get_function_name, get_wrapper_name, set_wrapper_name


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

@overload
def handle_error[T](
	func: Callable[..., T],
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0
) -> Callable[..., T]: ...

@overload
def handle_error[T](
	func: None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def handle_error[T](
	func: Callable[..., T] | None = None,
	*,
	exceptions: tuple[type[BaseException], ...] | type[BaseException] = (Exception,),
	message: str = "",
	error_log: LogLevels = LogLevels.WARNING_TRACEBACK,
	sleep_time: float = 0.0
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that handle an error with different log levels.

	Args:
		func        (Callable[..., T] | None):    	Function to decorate
		exceptions	(tuple[type[BaseException]], ...):	Exceptions to handle
		message		(str):								Message to display with the error. (e.g. "Error during something")
		error_log	(LogLevels):						Log level for the errors

			- :attr:`LogLevels.NONE` - None
			- :attr:`LogLevels.WARNING` - Show as warning
			- :attr:`LogLevels.WARNING_TRACEBACK` - Show as warning with traceback
			- :attr:`LogLevels.ERROR_TRACEBACK` - Show as error with traceback
			- :attr:`LogLevels.RAISE_EXCEPTION` - Raise exception

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
	if Cfg.FORCE_RAISE_EXCEPTION:
		error_log = LogLevels.RAISE_EXCEPTION

	def decorator(func: Callable[..., T]) -> Callable[..., T]:
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
					warning(f"{msg}Error during {get_function_name(func)}(): ({type(e).__name__}) {e}")
				elif error_log == LogLevels.WARNING_TRACEBACK:
					warning(f"{msg}Error during {get_function_name(func)}():\n{format_exc()}")
				elif error_log == LogLevels.ERROR_TRACEBACK:
					error(f"{msg}Error during {get_function_name(func)}():\n{format_exc()}", exit=True)
				elif error_log == LogLevels.RAISE_EXCEPTION:
					raise e

				# Sleep for the specified time, only if the error_log is not ERROR_TRACEBACK (because it's blocking)
				if sleep_time > 0.0 and error_log != LogLevels.ERROR_TRACEBACK:
					time.sleep(sleep_time)
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.handle_error", func))
		return wrapper

	# Handle both @handle_error and @handle_error(exceptions=..., message=..., error_log=...)
	if func is None:
		return decorator
	return decorator(func)

