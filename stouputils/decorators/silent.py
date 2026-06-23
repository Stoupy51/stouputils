
# Imports
from collections.abc import Callable, Sequence
from functools import wraps
from typing import Any, overload

from ..ctx.muffle import Muffle
from .common import get_wrapper_name, set_wrapper_name


# Decorator that make a function silent (disable stdout)
@overload
def silent[T](
	func: Callable[..., T],
	*,
	mute_stderr: bool = False,
	replay_on_error: bool = False,
	error_log_level: int | None = None,
	watch_loggers: Sequence[str] | None = None,
) -> Callable[..., T]: ...

@overload
def silent[T](
	func: None = None,
	*,
	mute_stderr: bool = False,
	replay_on_error: bool = False,
	error_log_level: int | None = None,
	watch_loggers: Sequence[str] | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def silent[T](
	func: Callable[..., T] | None = None,
	*,
	mute_stderr: bool = False,
	replay_on_error: bool = False,
	error_log_level: int | None = None,
	watch_loggers: Sequence[str] | None = None,
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that makes a function silent (disable stdout, and stderr if specified).

	Alternative to :py:class:`~stouputils.ctx.Muffle`.

	Args:
		func			(Callable[..., T] | None):	Function to make silent
		mute_stderr		(bool):						Whether to mute stderr or not
		replay_on_error	(bool):						Capture output and replay it if the call errors (see :py:class:`~stouputils.ctx.Muffle`)
		error_log_level	(int | None):				Also treat log records at/above this level as an error (e.g. ``logging.ERROR``)
		watch_loggers	(Sequence[str] | None):		Names of the loggers to watch for ``error_log_level`` (default: root logger only)

	Examples:
		>>> @silent
		... def test():
		...     print("Hello, world!")
		>>> test()

		>>> @silent(mute_stderr=True)
		... def test2():
		...     print("Hello, world!")
		>>> test2()

		>>> silent(print)("Hello, world!")

		>>> # Only shows the output if the wrapped call fails
		>>> @silent(replay_on_error=True)
		... def test3():
		...     print("Context that explains the failure below")
		...     raise ValueError("boom")
		>>> try:
		...     test3()
		... except ValueError:
		...     pass
		Context that explains the failure below
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Use Muffle context manager to silence output
			with Muffle(
				mute_stderr=mute_stderr,
				replay_on_error=replay_on_error,
				error_log_level=error_log_level,
				watch_loggers=watch_loggers,
			):
				return func(*args, **kwargs)
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.silent", func))
		return wrapper

	# Handle both @silent and @silent(mute_stderr=...)
	if func is None:
		return decorator
	return decorator(func)

