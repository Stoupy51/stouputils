
# Imports
import sys
from collections.abc import Callable
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
		values			(Any):		Values to print
		print_function	(Callable):	Function to use to print the values (default: debug())
		max_length		(int):		Maximum length of the value string to print (default: 250)
		color			(str):		Color of the message (default: CYAN)
		text			(str):		Text in the message (replaces "DEBUG")
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	def _internal(value: Any) -> str:
		""" Get the string representation of the value, with length or shape instead of length if shape is available """

		# Build metadata parts list
		metadata_parts: list[str] = []

		# Get attributes if available (with priority order)
		for attributes in [("dtype","dtypes"),("nbytes","memory_usage"),("device",)]:
			# Find the first available attribute of the current tuple
			for attr in attributes:
				try:
					attr_value = getattr(value, attr)
					if attr_value is not None:
						# Skip device if it's "cpu"
						if attr == "device" and str(attr_value).lower() == "cpu":
							break
						metadata_parts.append(f"{attr}: {attr_value}")
						break
				except (AttributeError, TypeError):
					continue

		# Get the shape or length of the value
		try:
			if value.shape:
				metadata_parts.append(f"shape: {value.shape}")
		except (AttributeError, TypeError):
			try:
				metadata_parts.append(f"length: {len(value)}")
			except (AttributeError, TypeError):
				pass

		# Get the min and max if available (Iterable of numbers)
		try:
			if not isinstance(value, str | bytes | bytearray | dict | int | float):
				import numpy as np
				mini, maxi = np.min(value), np.max(value) # type: ignore
				if mini != maxi:
					metadata_parts.append(f"min: {mini}")
					metadata_parts.append(f"max: {maxi}")
		except (Exception):
			pass

		# Combine metadata into a single parenthesized string
		metadata_str: str = f"({', '.join(metadata_parts)}) " if metadata_parts else ""

		# Get the string representation of the value
		value = cast(Any, value)
		value_str: str = str(value)
		if len(value_str) > max_length:
			value_str = value_str[:max_length] + "..."
		if "\n" in value_str:
			value_str = "\n" + value_str	# Add a newline before the value if there is a newline in it.

		# Return the formatted string
		return f"{type(value)}, <id {id(value)}>: {metadata_str}{value_str}"

	# Print the values
	if len(values) > 1:
		print_function("".join(f"\n  {_internal(value)}" for value in values), flush=flush, color=color, text=text, **print_kwargs)
	elif len(values) == 1:
		print_function(_internal(values[0]), flush=flush, color=color, text=text, **print_kwargs)

def breakpoint(*values: Any, print_function: Callable[..., None] = warning, flush: bool = True, text: str = "BREAKPOINT (press Enter)", **print_kwargs: Any) -> None:
	""" Breakpoint function, pause the program and print the values.

	Args:
		values			(Any):		Values to print
		print_function	(Callable):	Function to use to print the values (default: warning())
		text			(str):		Text in the message (replaces "WARNING")
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	file: TextIO = sys.stderr
	if "file" in print_kwargs:
		if isinstance(print_kwargs["file"], list):
			file = cast(TextIO, print_kwargs["file"][0])
		else:
			file = print_kwargs["file"]
	whatisit(*values, print_function=print_function, flush=flush, text=text, **print_kwargs)
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

