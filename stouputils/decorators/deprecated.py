
# Imports
from collections.abc import Callable
from functools import wraps
from traceback import format_exc
from typing import Any, overload

from ..print import error, warning
from .common import get_function_name, get_wrapper_name, set_wrapper_name
from .handle_error import LogLevels


# Decorator that marks a function as deprecated
@overload
def deprecated[T](
	func: Callable[..., T],
	*,
	message: str = "",
	version: str = "",
	error_log: LogLevels = LogLevels.WARNING
) -> Callable[..., T]: ...

@overload
def deprecated[T](
	func: None = None,
	*,
	message: str = "",
	version: str = "",
	error_log: LogLevels = LogLevels.WARNING
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def deprecated[T](
	func: Callable[..., T] | None = None,
	*,
	message: str = "",
	version: str = "",
	error_log: LogLevels = LogLevels.WARNING
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that marks a function as deprecated.

	Args:
		func        (Callable[..., T] | None): Function to mark as deprecated
		message     (str):                       Additional message to display with the deprecation warning
		version     (str):                       Version since when the function is deprecated (e.g. "v1.2.0")
		error_log   (LogLevels):                 Log level for the deprecation warning

			- :attr:`LogLevels.NONE` - None
			- :attr:`LogLevels.WARNING` - Show as warning
			- :attr:`LogLevels.WARNING_TRACEBACK` - Show as warning with traceback
			- :attr:`LogLevels.ERROR_TRACEBACK` - Show as error with traceback
			- :attr:`LogLevels.RAISE_EXCEPTION` - Raise exception

	Examples:
		>>> @deprecated
		... def old_function():
		...     pass

		>>> @deprecated(message="Use 'new_function()' instead", error_log=LogLevels.WARNING)
		... def another_old_function():
		...     pass
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Build deprecation message
			msg: str = f"Function '{get_function_name(func)}()' is deprecated"
			if version:
				msg += f" since {version}"
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
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.deprecated", func))
		return wrapper

	# Handle both @deprecated and @deprecated(message=..., error_log=...)
	if func is None:
		return decorator
	return decorator(func)

