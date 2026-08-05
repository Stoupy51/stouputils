
# Imports
from collections.abc import Callable
from pickle import dumps as pickle_dumps
from typing import Any, Literal, overload

from .common import get_wrapper_name, safe_wraps, set_wrapper_name

# Constants
ALL_CACHES: list[dict[Any, Any]] = []
""" Registry of every cache dict created by :func:`simple_cache`.
Call :func:`clear_simple_caches` to clear all of them at once.
"""

MISSING: Any = object()
""" Sentinel telling a cache miss apart from a cached ``None``, so a lookup costs one dict access instead of two. """

KWARGS_MARKER: tuple[object] = (object(),)
""" Separator inserted between args and kwargs by the "hash" method.
Being a unique object, it keeps ``f(1, b=2)`` from colliding with ``f(1, ("b", 2))``.
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
	method: Literal["hash", "str", "pickle"] | Callable[[tuple[Any, ...], dict[str, Any]], Any] = "hash"
) -> Callable[..., T]: ...

@overload
def simple_cache[T](
	func: None = None,
	*,
	method: Literal["hash", "str", "pickle"] | Callable[[tuple[Any, ...], dict[str, Any]], Any] = "hash"
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...

def simple_cache[T](
	func: Callable[..., T] | None = None,
	*,
	method: Literal["hash", "str", "pickle"] | Callable[[tuple[Any, ...], dict[str, Any]], Any] = "hash"
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
	""" Decorator that caches the result of a function based on its arguments.

	The default hash method is the fastest since it uses the arguments themselves as key, at the cost of two restrictions.
	It requires every argument to be hashable, and it shares one entry between equal keys such as 1, 1.0 and True.
	Switch to the str method for unhashable arguments, and to the pickle method for complex objects needing an exact key.
	The caching method is resolved once at decoration time, so an invalid one raises immediately instead of on first call.

	Args:
		func   (Callable[..., T] | None):			Function to cache
		method (Literal["hash", "str", "pickle"]):	The method to use for caching, or a callable building the key.

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

		The default hash method uses the arguments themselves as key, so the str method is needed for unhashable ones:
		>>> @simple_cache
		... def test4(a: list[int], b: int) -> int:
		...     return sum(a) + b
		>>> test4([1], 2)	# doctest: +ELLIPSIS
		Traceback (most recent call last):
		TypeError: ...unhashable type: 'list'...
		>>> @simple_cache(method="str")
		... def test5(a: list[int], b: int) -> int:
		...     return sum(a) + b
		>>> test5([1], 2)
		3

		Prevent a function from running more than once regardless of arguments:
		>>> @simple_cache(method=lambda x, y: 1)
		... def execute_one_time() -> None:
		...     print("Executed!")
		>>> _ = [execute_one_time() for _ in range(3)]
		Executed!

		An unknown method is rejected right away:
		>>> @simple_cache(method="json")	# doctest: +ELLIPSIS
		... def test3() -> None: ...
		Traceback (most recent call last):
		ValueError: Invalid caching method 'json'...
	"""
	# Reject an invalid method now so the wrappers below never have to check it again
	if not callable(method) and method not in ("hash", "str", "pickle"):
		raise ValueError(f"Invalid caching method {method!r}. Supported are 'hash', 'str', 'pickle' and any callable.")

	def decorator(func: Callable[..., T]) -> Callable[..., T]:
		# Create the cache dict and bind its lookup, hot path being a single dict access
		cache: dict[Any, T] = {}
		ALL_CACHES.append(cache)
		cache_get: Callable[[Any, Any], Any] = cache.get

		# Create the wrapper specialized for the requested method
		if callable(method):
			key_func: Callable[[tuple[Any, ...], dict[str, Any]], Any] = method

			@safe_wraps(func)
			def wrapper(*args: Any, **kwargs: Any) -> T:
				key: Any = key_func(args, kwargs)
				result: Any = cache_get(key, MISSING)
				if result is MISSING:
					cache[key] = result = func(*args, **kwargs)
				return result

		elif method == "hash":
			@safe_wraps(func)
			def wrapper(*args: Any, **kwargs: Any) -> T:
				key: Any = args if not kwargs else (*args, KWARGS_MARKER, *kwargs.items())
				result: Any = cache_get(key, MISSING)
				if result is MISSING:
					cache[key] = result = func(*args, **kwargs)
				return result

		elif method == "str":
			@safe_wraps(func)
			def wrapper(*args: Any, **kwargs: Any) -> T:
				key: str = str(args) if not kwargs else str(args) + str(kwargs)
				result: Any = cache_get(key, MISSING)
				if result is MISSING:
					cache[key] = result = func(*args, **kwargs)
				return result

		else:
			@safe_wraps(func)
			def wrapper(*args: Any, **kwargs: Any) -> T:
				key: bytes = pickle_dumps((args, kwargs))
				result: Any = cache_get(key, MISSING)
				if result is MISSING:
					cache[key] = result = func(*args, **kwargs)
				return result

		# Return the wrapper
		set_wrapper_name(wrapper, get_wrapper_name("stouputils.decorators.simple_cache", func))
		return wrapper

	# Handle both @simple_cache and @simple_cache(method=...)
	if func is None:
		return decorator
	return decorator(func)

