"""
This module provides utilities for typing enhancements such as JSON type aliases:

- :py:class:`JsonDict`
- :py:class:`JsonList`
- :py:class:`JsonMap`
- :py:class:`JsonMutMap`
- :py:class:`IterAny`
- :py:func:`convert_to_serializable`
"""

# Imports
from collections.abc import Iterable, Mapping, MutableMapping
from dataclasses import asdict, is_dataclass
from typing import Any, cast

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
		>>> convert_to_serializable(Point(3, 4))
		{'x': 3, 'y': 4}
	"""
	if hasattr(obj, "to_dict"):
		return obj.to_dict()
	elif is_dataclass(obj):
		return asdict(obj) # pyright: ignore[reportArgumentType]
	elif isinstance(obj, dict | Mapping | MutableMapping):
		return {k: convert_to_serializable(v) for k, v in cast(JsonDict, obj).items()}
	elif isinstance(obj, Iterable) and not isinstance(obj, (str, bytes)):
		return [convert_to_serializable(item) for item in cast(IterAny, obj)]
	return obj

