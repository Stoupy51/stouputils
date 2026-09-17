
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Callable
from typing import Any, overload


# Classes
class Registry[T: Any](dict[str, T]):
	""" Dictionary that registers callables by decorator. """

	def __init__(self, *args: Any, key_getter: Callable[[T], str] | None = None, **kwargs: Any) -> None:
		super().__init__(*args, **kwargs)
		self.key_getter: Callable[[T], str] | None = key_getter
		""" Callable taking an object and returning its key, or None to use the object's name. """

	@overload
	def register(self, function: T, /) -> T: ...

	@overload
	def register(self, *, name: str | None = None) -> Callable[[T], T]: ...

	def register(
		self,
		function: T | None = None,
		*,
		name: str | None = None,
	) -> T | Callable[[T], T]:
		""" Register a callable by its own name or a custom name.

		Python applies stacked decorators from bottom to top. Put ``register``
		outermost when the registry should keep the fully decorated callable.

		>>> FUNCS = Registry[Callable[[int], int]]()
		>>> from stouputils import measure_time
		>>> @FUNCS.register
		... @measure_time(printer=lambda *args: None)
		... def measured(value: int) -> int:
		... 	return value * 5
		>>> FUNCS["measured"] is measured
		True

		>>> @FUNCS.register
		... def double(value: int) -> int:
		... 	return value * 2
		>>> @FUNCS.register()
		... def triple(value: int) -> int:
		... 	return value * 3
		>>> @FUNCS.register(name="quadruple")
		... def multiply(value: int) -> int:
		... 	return value * 4

		>>> sorted(FUNCS), FUNCS["double"](2), FUNCS["quadruple"](2)
		(['double', 'measured', 'quadruple', 'triple'], 4, 8)

		>>> @FUNCS.register(name="double")
		... def another(value: int) -> int:
		... 	return value
		Traceback (most recent call last):
		...
		KeyError: "The name 'double' is already registered."
		"""
		def decorator(obj: T) -> T:
			key: str
			if name is not None:
				key = name
			elif self.key_getter is not None:
				key = self.key_getter(obj)
			elif hasattr(obj, "__name__"):
				key = obj.__name__
			else:
				raise TypeError(f"Cannot register {obj!r}: it has no name. Pass a name explicitly.")

			if key in self:
				raise KeyError(f"The name '{key}' is already registered.")

			self[key] = obj
			return obj

		if function is not None:
			if name is not None:
				raise TypeError("A custom name cannot be combined with direct registration.")
			return decorator(function)
		return decorator

