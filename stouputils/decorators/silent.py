
# Imports
from collections.abc import Callable
from functools import wraps
from typing import Any, overload

from ..ctx import Muffle
from .common import get_wrapper_name, set_wrapper_name


# Decorator that make a function silent (disable stdout)
@overload
def silent[T](
	func: Callable[..., T],
	*,
	mute_stderr: bool = False
) -> Callable[..., T]: ...

@overload
def silent[T](
	func: None = None,
	*,
	mute_stderr: bool = False
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def silent[T](
	func: Callable[..., T] | None = None,
	*,
	mute_stderr: bool = False
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that makes a function silent (disable stdout, and stderr if specified).

	Alternative to :py:class:`~stouputils.ctx.Muffle`.

	Args:
		func			(Callable[..., T] | None):	Function to make silent
		mute_stderr		(bool):						Whether to mute stderr or not

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
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:
			# Use Muffle context manager to silence output
			with Muffle(mute_stderr=mute_stderr):
				return func(*args, **kwargs)
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.silent", func))
		return wrapper

	# Handle both @silent and @silent(mute_stderr=...)
	if func is None:
		return decorator
	return decorator(func)

