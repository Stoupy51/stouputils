
""" Decorators marking how a class is meant to be extended.

:func:`inheritable` flags a class designed to be subclassed, :func:`overridable` a working default a subclass may replace,
and :func:`hook` a method called at a fixed point of a flow, whose default does nothing so a subclass can act there.
They only set a boolean attribute and never wrap what they decorate, so they cost nothing at call time.

.. code-block:: python

	@inheritable
	class Trainer:
		def fit(self) -> None:
			self.before_epoch()
			self.train_epoch()

		@hook
		def before_epoch(self) -> None: ...

		@overridable
		def train_epoch(self) -> None:
			...
"""
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

	Unlike :func:`hook`, the default already does the job, and a subclass swaps it for another way of doing it.
	Nothing is enforced at runtime and the member is not wrapped.
	Stack it above ``@property``, ``@classmethod`` or ``@staticmethod``: the flag lands on the underlying function.

	Examples:
		>>> class Base:
		...     @overridable
		...     def run(self) -> None: ...
		...
		...     @overridable
		...     @property
		...     def name(self) -> str: return "base"
		...
		...     @overridable
		...     @classmethod
		...     def create(cls) -> None:
		...         ...
		>>> Base.run.__is_overridable__, Base.name.fget.__is_overridable__, Base.create.__is_overridable__
		(True, True, True)
	"""
	set_member_flag(member, OVERRIDABLE_ATTRIBUTE)
	return member

## Hook
def hook[T: ClassMember](member: T) -> T:
	""" Mark a method as a hook, called at a fixed point of a flow, sets ``__is_hook__`` to True.

	The caller may be the class itself, or code driving it from outside, such as a trainer calling a model.
	Unlike :func:`overridable`, the default does nothing, or hands its input back unchanged: a subclass adds behaviour at that point.
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

