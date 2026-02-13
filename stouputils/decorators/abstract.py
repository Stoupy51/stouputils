
# Imports
from collections.abc import Callable
from functools import wraps
from typing import Any, overload

from .common import get_function_name, get_wrapper_name, set_wrapper_name
from .handle_error import LogLevels, handle_error


# Decorator that marks a function as abstract
@overload
def abstract[T](
	func: Callable[..., T],
	*,
	error_log: LogLevels = LogLevels.RAISE_EXCEPTION
) -> Callable[..., T]: ...

@overload
def abstract[T](
	func: None = None,
	*,
	error_log: LogLevels = LogLevels.RAISE_EXCEPTION
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def abstract[T](
	func: Callable[..., T] | None = None,
	*,
	error_log: LogLevels = LogLevels.RAISE_EXCEPTION
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that marks a function as abstract.

	Contrary to the :py:func:`abc.abstractmethod` decorator that raises a :py:exc:`TypeError`
	when you try to instantiate a class that has abstract methods, this decorator raises
	a :py:exc:`NotImplementedError` ONLY when the decorated function is called, indicating that the function
	must be implemented by a subclass.

	Args:
		func       (Callable[..., T] | None): The function to mark as abstract
		error_log  (LogLevels):               Log level for the error handling:

			- :attr:`LogLevels.NONE` - None
			- :attr:`LogLevels.WARNING` - Show as warning
			- :attr:`LogLevels.WARNING_TRACEBACK` - Show as warning with traceback
			- :attr:`LogLevels.ERROR_TRACEBACK` - Show as error with traceback
			- :attr:`LogLevels.RAISE_EXCEPTION` - Raise exception

	Examples:
		.. code-block:: python

			>>> class Base:
			...     @abstract
			...     def method(self):
			...         pass
			>>> Base().method()
			Traceback (most recent call last):
				...
			NotImplementedError: Function 'method()' is abstract and must be implemented by a subclass
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		message: str = f"Function '{get_function_name(func)}()' is abstract and must be implemented by a subclass"
		if not func.__doc__:
			func.__doc__ = message

		@wraps(func)
		@handle_error(exceptions=NotImplementedError, error_log=error_log)
		def not_implemented_error(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			raise NotImplementedError(message)
		set_wrapper_name(not_implemented_error, get_wrapper_name("stouputils.decorators.abstract", func))
		return not_implemented_error

	# Handle both @abstract and @abstract(error_log=...)
	if func is None:
		return decorator
	return decorator(func)

