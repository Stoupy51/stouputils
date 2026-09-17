
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Callable
from typing import overload


# Classes
class Registry[T: Callable[..., object]](dict[str, T]):
	""" Dictionary that registers callables by decorator. """

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
		def decorator(callable_: T) -> T:
			key: str = name if name is not None else callable_.__name__
			if key in self:
				raise KeyError(f"The name '{key}' is already registered.")
			self[key] = callable_
			return callable_

		if function is not None:
			if name is not None:
				raise TypeError("A custom name cannot be combined with direct registration.")
			return decorator(function)
		return decorator

