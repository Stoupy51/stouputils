
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from typing import Any

from .aliases import CallableAny

# Constants
INHERITABLE_ATTRIBUTE: str = "__is_inheritable__"
""" Attribute set to True on a class decorated with :func:`inheritable`. """
OVERRIDABLE_ATTRIBUTE: str = "__is_overridable__"
""" Attribute set to True on the function behind a member decorated with :func:`overridable`. """
HOOK_ATTRIBUTE: str = "__is_hook__"
""" Attribute set to True on the function behind a member decorated with :func:`hook`. """

# Typing aliases
type ClassMember = CallableAny | property | classmethod[Any, ..., Any] | staticmethod[..., Any]
""" A type alias for anything defined in a class body that can be decorated """


# Functions
## Inheritable
def inheritable[T: type[Any]](cls: T) -> T:
	""" Mark a class as meant to be subclassed, sets ``__is_inheritable__`` to True.

	Nothing is enforced at runtime: it only tells the reader that subclassing is part of the class contract.

	Examples:
		>>> @inheritable
		... class Base:
		...     pass
		>>> Base.__is_inheritable__
		True
	"""
	setattr(cls, INHERITABLE_ATTRIBUTE, True)
	return cls

## Overridable
def overridable[T: ClassMember](member: T) -> T:
	""" Mark a member as a default implementation that subclasses may replace, sets ``__is_overridable__`` to True.

	Nothing is enforced at runtime and the member is not wrapped.
	Stack it above ``@property``, ``@classmethod`` or ``@staticmethod``: the flag lands on the underlying function.

	Examples:
		>>> class Base:
		...     @overridable
		...     def run(self) -> None: ...
		...     @overridable
		...     @property
		...     def name(self) -> str: return "base"
		...     @overridable
		...     @classmethod
		...     def create(cls) -> None: ...
		>>> Base.run.__is_overridable__, Base.name.fget.__is_overridable__, Base.create.__is_overridable__
		(True, True, True)
	"""
	set_member_flag(member, OVERRIDABLE_ATTRIBUTE)
	return member

## Hook
def hook[T: ClassMember](member: T) -> T:
	""" Mark a method as a hook the base class calls at a fixed point of its flow, sets ``__is_hook__`` to True.

	Unlike :func:`overridable`, the base implementation is usually empty: subclasses fill it in rather than replace it.
	Nothing is enforced at runtime and the member is not wrapped.

	Examples:
		>>> class Runner:
		...     @hook
		...     def before_run(self) -> None: ...
		>>> Runner.before_run.__is_hook__
		True
	"""
	set_member_flag(member, HOOK_ATTRIBUTE)
	return member

## Set Member Flag
def set_member_flag(member: ClassMember, attribute: str) -> None:
	""" Set ``attribute`` to True on the function behind a class member.

	Args:
		member: Function, property (its getter is flagged), classmethod or staticmethod (their ``__func__`` is flagged)
	"""
	match member:
		case property(fget=getter):
			setattr(getter, attribute, True)
		case classmethod() | staticmethod():
			setattr(member.__func__, attribute, True)
		case _:
			setattr(member, attribute, True)

