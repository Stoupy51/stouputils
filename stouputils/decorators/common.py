
# Imports
from collections.abc import Callable
from functools import WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES
from typing import Any

from ..typing import CallableAny

# Constants
WRAPPED_ATTRIBUTE: str = "__wrapped__"
""" Attribute functools assigns last, so that :func:`inspect.signature` follows a wrapper back to the original. """


# "Private" functions
def safe_wraps[WrapperT: CallableAny](wrapped: Any) -> Callable[[WrapperT], WrapperT]:
	""" Tolerant replacement for :func:`functools.wraps`, copying only the metadata that can actually be copied.

	``functools.wraps`` assigns ``__type_params__`` among other attributes, and a function object rejects any value
	that is not a tuple.
	Decorating an object whose attributes are synthesised, such as a Sphinx autodoc mock, therefore raises
	``TypeError`` and takes down the import of every module that touches the decorated symbol.
	Skipping the attributes that refuse to be copied keeps the decorator working on anything callable.

	Args:
		wrapped (Any): Object the wrapper stands for
	Returns:
		Callable[[WrapperT], WrapperT]: Decorator applying the metadata to a wrapper

	Examples:
		>>> def original(a: int) -> int:
		...     ''' Doc. '''
		...     return a
		>>> @safe_wraps(original)
		... def wrapper(*args: Any, **kwargs: Any) -> int: ...
		>>> wrapper.__name__, wrapper.__doc__.strip()
		('original', 'Doc.')

		An attribute a function refuses is skipped, where functools.wraps would raise TypeError:
		>>> class Synthetic:
		...     __type_params__ = "not a tuple"
		>>> @safe_wraps(Synthetic())
		... def survivor() -> None: ...
		>>> survivor.__name__
		'survivor'
	"""
	def decorator(wrapper: WrapperT) -> WrapperT:
		for attribute in WRAPPER_ASSIGNMENTS:
			try:
				setattr(wrapper, attribute, getattr(wrapped, attribute))
			except (AttributeError, TypeError):
				continue
		for attribute in WRAPPER_UPDATES:
			try:
				getattr(wrapper, attribute).update(getattr(wrapped, attribute, {}))
			except (AttributeError, TypeError):
				continue

		setattr(wrapper, WRAPPED_ATTRIBUTE, wrapped)
		return wrapper

	return decorator


def get_function_name(func: CallableAny) -> str:
	""" Get the name of a function, returns "<unknown>" if the name cannot be retrieved. """
	try:
		return func.__name__
	except AttributeError:
		return "<unknown>"

def get_wrapper_name(decorator_name: str, func: CallableAny) -> str:
	""" Get a descriptive name for a wrapper function.

	Args:
		decorator_name	(str):					Name of the decorator
		func			(CallableAny):			Function being decorated
	Returns:
		str: Combined name for the wrapper function (e.g., "stouputils.decorators.handle_error@function_name")
	"""
	func_name: str = get_function_name(func)

	# Remove "stouputils.decorators.*" prefix if present
	if func_name.startswith("stouputils.decorators."):
		func_name = func_name.split(".", 2)[-1]

	return f"{decorator_name}@{func_name}"


def set_wrapper_name(wrapper: CallableAny, name: str) -> None:
	""" Set the wrapper function's visible name (code object name) for clearer tracebacks.

	Args:
		wrapper	(CallableAny):	Wrapper function to update
		name	(str):			New name to set
	"""
	# Update the code object's co_name so tracebacks show the new name
	try:
		wrapper.__code__ = wrapper.__code__.replace(co_name=name)
	except Exception:
		# If code.replace isn't available, ignore silently
		pass

