
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import sys
from collections.abc import Callable
from contextlib import suppress
from typing import Any, TextIO, cast

from ..config import StouputilsConfig as Cfg
from .message import debug, warning


def whatisit(
	*values: Any,
	print_function: Callable[..., None] = debug,
	flush: bool = True,
	max_length: int = 250,
	color: str = Cfg.CYAN,
	text: str = "What is it?",
	**print_kwargs: Any,
) -> None:
	""" Print the type of each value and the value itself, with its id and length/shape.

	The output format is: "type, <id id_number>:	(length/shape) value"

	Args:
		values:         Values to print
		print_function: Function to use to print the values (default: debug())
		max_length:     Maximum length of the value string to print (default: 250)
		color:          Color of the message (default: CYAN)
		text:           Text in the message (replaces "DEBUG")
		print_kwargs:   Keyword arguments to pass to the print function
	"""
	if "file" not in print_kwargs:
		print_kwargs["file"] = sys.stderr
	if len(values) > 1:
		lines: str = "".join(f"\n  {describe_value(value, max_length)}" for value in values)
		print_function(lines, flush=flush, color=color, text=text, **print_kwargs)
	elif len(values) == 1:
		print_function(describe_value(values[0], max_length), flush=flush, color=color, text=text, **print_kwargs)


def describe_value(value: Any, max_length: int = 250) -> str:
	""" The line :func:`whatisit` prints for one value: ``type, <id id_number>: (metadata) value``.

	Args:
		max_length: Characters of the value's string kept, the rest being replaced by ``...``.
	"""
	metadata: list[str] = value_metadata(value)
	metadata_str: str = f"({', '.join(metadata)}) " if metadata else ""
	value_str: str = str(value)
	if len(value_str) > max_length:
		value_str = value_str[:max_length] + "..."
	if "\n" in value_str:
		value_str = "\n" + value_str
	return f"{type(value)}, <id {id(value)}>: {metadata_str}{value_str}"


def value_metadata(value: Any) -> list[str]:
	""" What a value exposes among dtype, size in bytes, device, shape or length, and its min and max, as ``"name: value"``.

	A CPU device is left out, and min and max only appear when they differ.

	>>> value_metadata([1, 5, 3])
	['length: 3', 'min: 1', 'max: 5']
	>>> value_metadata("abc")
	['length: 3']
	"""
	metadata: list[str] = [
		entry for names in (("dtype", "dtypes"), ("nbytes", "memory_usage"), ("device",))
		if (entry := first_attribute_entry(value, names)) is not None
	]

	# Get the shape or length of the value
	try:
		if value.shape:
			metadata.append(f"shape: {value.shape}")
	except (AttributeError, TypeError):
		with suppress(AttributeError, TypeError):
			metadata.append(f"length: {len(value)}")

	# Get the min and max if available (Iterable of numbers)
	with suppress(Exception):
		if not isinstance(value, str | bytes | bytearray | dict | int | float):
			import numpy as np
			mini, maxi = np.min(value), np.max(value)
			if mini != maxi:
				metadata += [f"min: {mini}", f"max: {maxi}"]
	return metadata


def first_attribute_entry(value: Any, names: tuple[str, ...]) -> str | None:
	""" ``"name: value"`` for the first of these attributes the value holds, None when it holds none or its device is the CPU. """
	for name in names:
		try:
			attribute: Any = getattr(value, name)
			if attribute is None:
				continue
			return None if name == "device" and str(attribute).lower() == "cpu" else f"{name}: {attribute}"
		except (AttributeError, TypeError):
			continue
	return None

def breakpoint(
	*values: Any,
	print_function: Callable[..., None] = warning,
	flush: bool = True,
	max_length: int = 1000,
	color: str = Cfg.CYAN,
	text: str = "BREAKPOINT (press Enter)",
	**print_kwargs: Any
) -> None:
	""" Breakpoint function, pause the program and print the values.

	Args:
		values:         Values to print
		print_function: Function to use to print the values (default: warning())
		max_length:     Maximum length of the value string to print (default: 1000)
		color:          Color of the message (default: CYAN)
		text:           Text in the message (replaces "WARNING")
		print_kwargs:   Keyword arguments to pass to the print function
	"""
	file: TextIO = sys.stderr
	if "file" in print_kwargs:
		file = cast(TextIO, print_kwargs["file"][0]) if isinstance(print_kwargs["file"], list) else print_kwargs["file"]
	whatisit(*values, print_function=print_function, flush=flush, text=text, max_length=max_length, color=color, **print_kwargs)
	try:
		input()
	except (KeyboardInterrupt, EOFError):
		print(file=file)
		sys.exit(1)




# Convenience colored functions
def whatisitc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return whatisit(*args, use_colored=use_colored, **kwargs)
def breakpointc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return breakpoint(*args, use_colored=use_colored, **kwargs)

