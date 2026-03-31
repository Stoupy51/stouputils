"""
This module provides utilities for typing enhancements such as JSON type aliases:

- :py:class:`JsonDict`
- :py:class:`JsonList`
- :py:class:`JsonMap`
- :py:class:`JsonMutMap`
- :py:class:`IterAny`
- :py:class:`CallableAny`
- :py:class:`ClassInfo`
- :py:func:`is_generic_instance`
- :py:func:`convert_to_serializable`
"""

# Imports
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from dataclasses import asdict, is_dataclass
from types import GenericAlias, UnionType
from typing import Any, TypeAliasType, TypeGuard, cast, get_origin, overload

# Typing aliases
type JsonDict = dict[str, Any]
""" A type alias for JSON dictionaries """
type JsonList = list[Any]
""" A type alias for JSON lists """
type JsonMap = Mapping[str, Any]
""" A type alias for JSON mapping """
type JsonMutMap = MutableMapping[str, Any]
""" A type alias for mutable JSON mapping """
type IterAny = Iterable[Any]
""" A type alias for iterable of any type """
type CallableAny = Callable[..., Any]
""" A type alias for any callable """

type ClassInfo = type[Any] | UnionType | GenericAlias | tuple[ClassInfo, ...]
""" A type alias for class information used in isinstance checks, including unions and tuples of classes """

# Functions
@overload
def is_generic_instance[T](obj: Any, type_hint: type[T]) -> TypeGuard[T]: ...
@overload
def is_generic_instance(obj: Any, type_hint: UnionType) -> TypeGuard[Any]: ...
@overload
def is_generic_instance[T: tuple[ClassInfo, ...]](obj: Any, type_hint: T) -> TypeGuard[T]: ...
@overload
def is_generic_instance[T: GenericAlias](obj: Any, type_hint: T) -> TypeGuard[T]: ...
@overload
def is_generic_instance(obj: Any, type_hint: Any) -> TypeGuard[Any]: ...

def is_generic_instance(obj: Any, type_hint: Any) -> TypeGuard[Any]:
	""" Runtime equivalent of isinstance() for generic type hints.
	If you want to check types in a dict, you can use this function ``is_generic_instance(my_dict, dict[str, int])``
	to check if `my_dict` is a dictionary with string keys and integer values.

	### Note: this function is not a perfect replacement for static type checking and may not cover all edge cases or complex type hints.

	Args:
		obj			(Any): The object to check.
		type_hint	(Any): The type hint to check against.
	Returns:
		True if `obj` matches `type_hint`, False otherwise.
	Examples:
		>>> is_generic_instance(5, int)
		True
		>>> is_generic_instance("hello", str)
		True
		>>> is_generic_instance([1, 2, 3], list)
		True
		>>> is_generic_instance([1, 2, 3], list[int])
		True
		>>> is_generic_instance([1, 2, 3], list[str])
		False
		>>> is_generic_instance({"a": 1}, dict[str, int])
		True
		>>> is_generic_instance({"a": 1}, dict[str, int] | Mapping)
		True
		>>> is_generic_instance({"a": 1}, dict[str, int] | Mapping | JsonDict)
		True
		>>> is_generic_instance({"a": 1}, (dict[str, int], Mapping, JsonDict))
		True
		>>> is_generic_instance([1, 2, 3], dict[str, int])
		False
		>>> is_generic_instance({"a": 1}, "dict[str, int] | Mapping | JsonDict")
		True
	"""
	while isinstance(type_hint, TypeAliasType):
		type_hint = type_hint.__value__
	if isinstance(type_hint, str):
		try:
			type_hint = eval(type_hint, globals())
		except Exception:
			return False
	if type_hint is Any:
		return True
	if isinstance(type_hint, UnionType):
		return any(is_generic_instance(obj, t) for t in type_hint.__args__)
	if isinstance(type_hint, tuple):
		return any(is_generic_instance(obj, t) for t in cast(Any, type_hint))
	if isinstance(type_hint, GenericAlias):
		origin = get_origin(type_hint)
		if not isinstance(obj, origin):
			return False
		args = type_hint.__args__
		if len(args) == 1:
			return all(is_generic_instance(item, args[0]) for item in obj)
		elif len(args) == 2 and isinstance(obj, dict | Mapping | MutableMapping):
			return all(is_generic_instance(val, typ) for k, v in cast(JsonDict, obj).items() for val, typ in zip((k, v), args, strict=True))
		return True
	return isinstance(obj, type_hint)


## Utility functions
def convert_to_serializable(obj: Any) -> Any:
	""" Recursively convert objects to JSON-serializable forms.

	Objects with a `to_dict()` or `asdict()` method are converted to their dictionary representation.
	Dictionaries and lists are recursively processed.

	Can also be used to convert nested structures containing custom objects,
	such as defaultdict, dataclasses, or other user-defined types.

	Args:
		obj (Any): The object to convert
	Returns:
		Any: The JSON-serializable version of the object
	Examples:
		>>> from typing import defaultdict
		>>> my_dict = defaultdict(lambda: defaultdict(int))
		>>> my_dict['a']['b'] += 6
		>>> my_dict['c']['d'] = 4
		>>> my_dict['a']
		defaultdict(<class 'int'>, {'b': 6})
		>>> my_dict['c']
		defaultdict(<class 'int'>, {'d': 4})
		>>> convert_to_serializable(my_dict)
		{'a': {'b': 6}, 'c': {'d': 4}}

		>>> from dataclasses import dataclass
		>>> @dataclass
		... class Point:
		...     x: int
		...     y: int
		...     some_list: list[int]
		>>> convert_to_serializable(Point(3, 4, [1, 2, 3]))
		{'x': 3, 'y': 4, 'some_list': [1, 2, 3]}
	"""
	if hasattr(obj, "to_dict"):
		return obj.to_dict()
	elif is_dataclass(obj):
		return asdict(obj) # pyright: ignore[reportArgumentType]
	elif is_generic_instance(obj, JsonDict | Mapping | MutableMapping):
		return {k: convert_to_serializable(v) for k, v in obj.items()}
	elif is_generic_instance(obj, IterAny) and not isinstance(obj, (str, bytes)):
		return [convert_to_serializable(item) for item in obj]
	return obj

