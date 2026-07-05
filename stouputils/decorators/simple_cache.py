
# Imports
from collections.abc import Callable
from functools import wraps
from pickle import dumps as pickle_dumps
from typing import Any, Literal, overload

from .common import get_wrapper_name, set_wrapper_name

# Imports
ALL_CACHES: list[dict[Any, Any]] = []
""" Registry of every cache dict created by :func:`simple_cache`.
Call :func:`clear_simple_caches` to clear all of them at once.
"""


def clear_simple_caches() -> None:
	""" Clear every cache created by :func:`simple_cache`.

	Useful for long-lived processes that run the same code on changing state:
	call this at the start of each cycle so cached results (and skipped side effects)
	from a previous cycle can't leak into the next one.

	Examples:
		>>> @simple_cache
		... def count_calls(x: int, _calls: list[int] = []) -> int:
		...     _calls.append(x)
		...     return len(_calls)
		>>> count_calls(1), count_calls(1)
		(1, 1)
		>>> clear_simple_caches()
		>>> count_calls(1)
		2
	"""
	for cache in ALL_CACHES:
		cache.clear()


# Easy cache function with parameter caching method
@overload
def simple_cache[T](
	func: Callable[..., T],
	*,
	method: Literal["str", "pickle"] | Callable[[tuple[Any, ...], dict[str, Any]], Any] = "str"
) -> Callable[..., T]: ...

@overload
def simple_cache[T](
	func: None = None,
	*,
	method: Literal["str", "pickle"] | Callable[[tuple[Any, ...], dict[str, Any]], Any] = "str"
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def simple_cache[T](
	func: Callable[..., T] | None = None,
	*,
	method: Literal["str", "pickle"] | Callable[[tuple[Any, ...], dict[str, Any]], Any] = "str"
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that caches the result of a function based on its arguments.

	The str method is often faster than the pickle method (by a little) but not as accurate with complex objects.

	Args:
		func   (Callable[..., T] | None): Function to cache
		method (Literal["str", "pickle"]):  The method to use for caching.

	Examples:
		>>> @simple_cache
		... def test1(a: int, b: int) -> int:
		...     return a + b

		>>> @simple_cache(method="str")
		... def test2(a: int, b: int) -> int:
		...     return a + b
		>>> test2(1, 2)
		3
		>>> test2(1, 2)
		3
		>>> test2(3, 4)
		7

		Cache a recursive function:
		>>> @simple_cache
		... def factorial(n: int) -> int:
		...     return n * factorial(n - 1) if n else 1
		>>> factorial(10)   # no previously cached result, makes 11 recursive calls
		3628800
		>>> factorial(5)    # no new calls, just returns the cached result
		120
		>>> factorial(12)   # two new recursive calls, factorial(10) is cached
		479001600

		Prevent a function from running more than once regardless of arguments:
		>>> @simple_cache(method=lambda x, y: 1)
		... def execute_one_time() -> None:
		...     print("Executed!")
		>>> _ = [execute_one_time() for _ in range(3)]
		Executed!
	"""
	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		# Create the cache dict
		cache_dict: dict[Any, Any] = {}
		ALL_CACHES.append(cache_dict)

		# Create the wrapper
		@wraps(func)
		def wrapper(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> Any:

			# Get the hashed key
			if method == "str":
				hashed = str(args) + str(kwargs)
			elif method == "pickle":
				hashed = pickle_dumps((args, kwargs))
			elif callable(method):
				hashed = method(args, kwargs)
			else:
				raise ValueError("Invalid caching method. Supported methods are 'str' and 'pickle'.")

			# If the key is in the cache, return it
			if hashed in cache_dict:
				return cache_dict[hashed]

			# Else, call the function and add the result to the cache
			else:
				result: Any = func(*args, **kwargs)
				cache_dict[hashed] = result
				return result

		# Return the wrapper
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.simple_cache", func))
		return wrapper

	# Handle both @simple_cache and @simple_cache(method=...)
	if func is None:
		return decorator
	return decorator(func)

