""" Registries map names to objects registered by decorator.
They replace a hand-written dictionary kept next to the functions it lists:

.. code-block:: python

	def foo(bar: int) -> int:
		return bar * 5
	def another_foo(bar: int) -> int:
		return bar * 2

	FOO_REGISTRY: dict[str, Callable[[int], int]] = {
		"foo": foo,
		"baz": another_foo,
	}

with:

.. code-block:: python

	FOO_REGISTRY = Registry[Callable[[int], int]]()

	@FOO_REGISTRY
	def foo(bar: int) -> int:
		return bar * 5

	@FOO_REGISTRY(name="baz")
	def another_foo(bar: int) -> int:
		return bar * 2
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, overload

# Lazy imports for typing
if TYPE_CHECKING:
	from _typeshed import SupportsKeysAndGetItem


# Classes
class Registry[T: Any](dict[str, T]):
	""" Dictionary that registers any object by decorator.

	>>> FUNCS = Registry[Callable[[int], int]]()
	>>> from stouputils import handle_error
	>>> @FUNCS.register
	... @handle_error
	... def measured(value: int) -> int: return value * 5
	>>> FUNCS["measured"] is measured
	True

	>>> FUNCS = Registry[Callable[[int], int]]()
	>>> @FUNCS(name="tripled")
	... def triple(value: int) -> int: return value * 3
	>>> FUNCS["tripled"](4)
	12

	>>> class Shape:
	... 	@classmethod
	... 	def get_name(cls) -> str: return cls.__name__.lower()
	>>> SHAPES = Registry[type[Shape]](key_getter=lambda cls: cls.get_name())
	>>> @SHAPES.register
	... class Circle(Shape): pass
	>>> @SHAPES.register(name="square")
	... class Square(Shape): pass
	>>> sorted(SHAPES), SHAPES["circle"] is Circle
	(['circle', 'square'], True)

	>>> @SHAPES.register()
	... class NotAShape: pass
	Traceback (most recent call last):
	...
	AttributeError: type object 'NotAShape' has no attribute 'get_name'

	>>> @SHAPES.register(name="circle")
	... class Duplicate(Shape): pass
	Traceback (most recent call last):
	...
	KeyError: "The name 'circle' is already registered."
	"""

	def __init__(
		self,
		entries: "SupportsKeysAndGetItem[str, T] | Iterable[tuple[str, T]]" = (),
		/,
		*,
		key_getter: Callable[[T], str] | None = None,
		**kwargs: T
	) -> None:
		super().__init__(entries, **kwargs)
		self.key_getter: Callable[[T], str] | None = key_getter
		""" Callable taking an object and returning its key, or None to use the object's name. """

	@overload
	def __call__(self, function: T, /) -> T: ...

	@overload
	def __call__(self, *, name: str | None = None, aliases: list[str] | None = None) -> Callable[[T], T]: ...

	def __call__(
		self,
		function: T | None = None,
		*,
		name: str | None = None,
		aliases: list[str] | None = None
	) -> T | Callable[[T], T]:
		""" Register an object using the registry itself as a decorator. """
		if function is not None:
			return self.register(function, name=name, aliases=aliases)
		return self.register(name=name, aliases=aliases)

	@overload
	def register(self, function: T, *, name: str | None = None, aliases: list[str] | None = None) -> T: ...

	@overload
	def register(self, *, name: str | None = None, aliases: list[str] | None = None) -> Callable[[T], T]: ...

	def register(
		self,
		function: T | None = None,
		*,
		name: str | None = None,
		aliases: list[str] | None = None
	) -> T | Callable[[T], T]:
		""" Register any object by its own name or a custom name.

		Python applies stacked decorators from bottom to top. Put ``register``
		outermost when the registry should keep the fully decorated object.
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

			destinations: list[str] = [key, *([] if not aliases else aliases)]
			for dest_key in destinations:
				if dest_key in self:
					raise KeyError(f"The name '{dest_key}' is already registered.")
				self[dest_key] = obj

			return obj

		if function is not None:
			if name is not None:
				raise TypeError("A custom name cannot be combined with direct registration.")
			return decorator(function)
		return decorator


	def __getitem__(self, key: str) -> T:
		""" Override the default getitem to show the available keys. """
		try:
			return super().__getitem__(key)
		except KeyError as e:
			raise KeyError(f"The name '{key}' is not registered, available keys: {', '.join(self.keys())}") from e

