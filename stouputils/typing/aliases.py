
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Callable, Iterable, Mapping, MutableMapping
from types import GenericAlias, UnionType
from typing import Any

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

