"""
This module provides utilities for typing enhancements:

- :py:class:`~aliases.JsonDict`, :py:class:`~aliases.JsonList`, :py:class:`~aliases.JsonMap`, :py:class:`~aliases.JsonMutMap` - Type aliases for JSON data
- :py:class:`~aliases.IterAny`, :py:class:`~aliases.CallableAny`, :py:class:`~aliases.ClassInfo` - Type aliases for iterables, callables and isinstance checks
- :py:func:`~runtime.is_generic_instance` - Runtime equivalent of isinstance() for generic type hints like ``dict[str, int]``
- :py:func:`~runtime.is_sequence` - Check if an object supports O(1) ``__len__`` and ``__getitem__``
- :py:func:`~runtime.convert_to_serializable` - Recursively convert objects (dataclasses, defaultdicts, ...) to JSON-serializable forms
- :py:deco:`~extension_points.inheritable` - Mark a class as meant to be subclassed
- :py:deco:`~extension_points.overridable` - Mark a member as a default implementation that subclasses may replace
- :py:deco:`~extension_points.hook` - Mark a method as a hook the base class calls at a fixed point of its flow
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .aliases import (
	CallableAny as CallableAny,
	ClassInfo as ClassInfo,
	IterAny as IterAny,
	JsonDict as JsonDict,
	JsonList as JsonList,
	JsonMap as JsonMap,
	JsonMutMap as JsonMutMap,
)
from .extension_points import (
	HOOK_ATTRIBUTE as HOOK_ATTRIBUTE,
	INHERITABLE_ATTRIBUTE as INHERITABLE_ATTRIBUTE,
	OVERRIDABLE_ATTRIBUTE as OVERRIDABLE_ATTRIBUTE,
	ClassMember as ClassMember,
	hook as hook,
	inheritable as inheritable,
	overridable as overridable,
	set_member_flag as set_member_flag,
)
from .runtime import (
	convert_to_serializable as convert_to_serializable,
	is_generic_instance as is_generic_instance,
	is_sequence as is_sequence,
)

