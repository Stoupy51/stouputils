
# Imports
from collections.abc import Callable
from typing import Any


# "Private" functions
def get_function_name(func: Callable[..., Any]) -> str:
	""" Get the name of a function, returns "<unknown>" if the name cannot be retrieved. """
	try:
		return func.__name__
	except AttributeError:
		return "<unknown>"

def get_wrapper_name(decorator_name: str, func: Callable[..., Any]) -> str:
	""" Get a descriptive name for a wrapper function.

	Args:
		decorator_name	(str):					Name of the decorator
		func			(Callable[..., Any]):	Function being decorated
	Returns:
		str: Combined name for the wrapper function (e.g., "stouputils.decorators.handle_error@function_name")
	"""
	func_name: str = get_function_name(func)

	# Remove "stouputils.decorators.*" prefix if present
	if func_name.startswith("stouputils.decorators."):
		func_name = func_name.split(".", 2)[-1]

	return f"{decorator_name}@{func_name}"


def set_wrapper_name(wrapper: Callable[..., Any], name: str) -> None:
	""" Set the wrapper function's visible name (code object name) for clearer tracebacks.

	Args:
		wrapper	(Callable[..., Any]):	Wrapper function to update
		name	(str):					New name to set
	"""
	# Update the code object's co_name so tracebacks show the new name
	try:
		wrapper.__code__ = wrapper.__code__.replace(co_name=name)
	except Exception:
		# If code.replace isn't available, ignore silently
		pass

