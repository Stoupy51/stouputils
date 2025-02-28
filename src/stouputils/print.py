"""
This module provides utility functions for printing messages with different levels of importance.

If a message is printed multiple times, it will be displayed as "(xN) message" where N is the number of times the message has been printed.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/print_module.gif
  :alt: stouputils print examples
"""

# Imports
import sys
import time
from typing import Callable, TextIO, IO, Any

# Colors constants
RESET: str   = "\033[0m"
RED: str     = "\033[91m"
GREEN: str   = "\033[92m"
YELLOW: str  = "\033[93m"
BLUE: str    = "\033[94m"
MAGENTA: str = "\033[95m"
CYAN: str    = "\033[96m"
LINE_UP: str = "\033[1A"

# Logging utilities
logging_to: set[IO[Any]] = set()	# Used by LogToFile context manager

def remove_colors(text: str) -> str:
	""" Remove the colors from a text """
	for color in [RESET, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, LINE_UP]:
		text = text.replace(color, "")
	return text

# Print functions
previous_args_kwards: tuple[Any, Any] = ((), {})
nb_values: int = 1

def is_same_print(*args: Any, **kwargs: Any) -> bool:
	""" Checks if the current print call is the same as the previous one. """
	global previous_args_kwards, nb_values
	if previous_args_kwards == (args, kwargs):
		nb_values += 1
		return True
	else:
		previous_args_kwards = (args, kwargs)
		nb_values = 1
		return False

import_time: float = time.time()
def current_time() -> str:
	# If the import time is more than 24 hours, return the full datetime
	if (time.time() - import_time) > (24 * 60 * 60):
		return time.strftime("%Y-%m-%d %H:%M:%S")
	else:
		return time.strftime("%H:%M:%S")

def info(*values: Any, color: str = GREEN, text: str = "INFO ", prefix: str = "", file: TextIO|list[TextIO]|None = None, **print_kwargs: Any) -> None:
	""" Print an information message looking like "[INFO HH:MM:SS] message" in green by default.

	Args:
		values			(Any):					Values to print (like the print function)
		color			(str):					Color of the message (default: GREEN)
		text			(str):					Text of the message (default: "INFO ")
		prefix			(str):					Prefix to add to the values
		file			(TextIO|list[TextIO]):	File(s) to write the message to (default: sys.stdout)
		print_kwargs	(dict):					Keyword arguments to pass to the print function
	"""
	if file is None:
		file = sys.stdout
	if isinstance(file, list):
		for f in file:
			info(*values, color=color, text=text, prefix=prefix, file=f, **print_kwargs)
	else:
		message: str = f"{prefix}{color}[{text} {current_time()}]"
		if is_same_print(*values, color=color, text=text, prefix=prefix, **print_kwargs):
			message = f"{LINE_UP}{message} (x{nb_values})"

		# Print normally with colors, and log to any registered logging files without colors
		print(message, *values, RESET, file=file, **print_kwargs)
		if logging_to:
			print_kwargs["flush"] = True
			for log_file in logging_to:
				print(remove_colors(message), *(remove_colors(str(v)) for v in values), file=log_file, **print_kwargs)

def debug(*values: Any, **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "DEBUG"
	if "color" not in print_kwargs:
		print_kwargs["color"] = BLUE
	info(*values, **print_kwargs)

def suggestion(*values: Any, **print_kwargs: Any) -> None:
	""" Print a suggestion message looking like "[SUGGESTION HH:MM:SS] message" """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "SUGGESTION"
	if "color" not in print_kwargs:
		print_kwargs["color"] = CYAN
	info(*values, **print_kwargs)

def progress(*values: Any, **print_kwargs: Any) -> None:
	""" Print a progress message looking like "[PROGRESS HH:MM:SS] message" """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "PROGRESS"
	if "color" not in print_kwargs:
		print_kwargs["color"] = MAGENTA
	info(*values, **print_kwargs)

def warning(*values: Any, **print_kwargs: Any) -> None:
	""" Print a warning message looking like "[WARNING HH:MM:SS] message" in sys.stderr """
	if "file" not in print_kwargs:
		print_kwargs["file"] = sys.stderr
	if "text" not in print_kwargs:
		print_kwargs["text"] = "WARNING"
	if "color" not in print_kwargs:
		print_kwargs["color"] = YELLOW
	info(*values, **print_kwargs)

def error(*values: Any, exit: bool = True, **print_kwargs: Any) -> None:
	""" Print an error message (in sys.stderr) and optionally ask the user to continue or stop the program

	Args:
		values			(Any):		Values to print (like the print function)
		exit			(bool):		Whether to ask the user to continue or stop the program, false to ignore the error automatically and continue
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	file: TextIO = sys.stderr
	if "file" in print_kwargs:
		if isinstance(print_kwargs["file"], list):
			file_list: list[TextIO] = print_kwargs["file"]
			file = file_list[0]
		else:
			file = print_kwargs["file"]
	if "text" not in print_kwargs:
		print_kwargs["text"] = "ERROR"
	if "color" not in print_kwargs:
		print_kwargs["color"] = RED
	info(*values, **print_kwargs)
	if exit:
		try:
			print("Press enter to ignore error and continue, or 'CTRL+C' to stop the program... ", file=file)
			input()
		except (KeyboardInterrupt, EOFError):
			print(file=file)
			sys.exit(1)

def whatisit(*values: Any, print_function: Callable[..., None] = debug, max_length: int = 250, **print_kwargs: Any) -> None:
	""" Print the type of each value and the value itself, with its id and length/shape.

	The output format is: "type, <id id_number>:	(length/shape) value"

	Args:
		values			(Any):		Values to print
		print_function	(Callable):	Function to use to print the values (default: debug())
		max_length		(int):		Maximum length of the value string to print (default: 250)
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	def _internal(value: Any) -> str:
		""" Get the string representation of the value, with length or shape instead of length if shape is available """
		length: str = ""
		try:
			length = f"(length: {len(value)}) "
		except (AttributeError, TypeError):
			pass
		try:
			length = f"(shape: {value.shape}) "
		except (AttributeError, TypeError):
			pass
		value_str: str = str(value)
		if len(value_str) > max_length:
			value_str = value_str[:max_length] + "..."
		if "\n" in value_str:
			length = "\n" + length	# Add a newline before the length if there is a newline in the value.
		return f"{type(value)}, <id {id(value)}>: {length}{value_str}"

	# Print
	if len(values) > 1:
		print_function("(What is it?)", **print_kwargs)
		for value in values:
			print_function(_internal(value), **print_kwargs)
	elif len(values) == 1:
		print_function(f"(What is it?) {_internal(values[0])}", **print_kwargs)

def breakpoint(*values: Any, print_function: Callable[..., None] = warning, **print_kwargs: Any) -> None:
	""" Breakpoint function, pause the program and print the values.

	Args:
		values			(Any):		Values to print
		print_function	(Callable):	Function to use to print the values (default: warning())
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	if "text" not in print_kwargs:
		print_kwargs["text"] = "BREAKPOINT (press Enter)"
	file: TextIO = sys.stderr
	if "file" in print_kwargs:
		if isinstance(print_kwargs["file"], list):
			file_list: list[TextIO] = print_kwargs["file"]
			file = file_list[0]
		else:
			file = print_kwargs["file"]
	whatisit(*values, print_function=print_function, **print_kwargs)
	try:
		input()
	except (KeyboardInterrupt, EOFError):
		print(file=file)
		sys.exit(1)






if __name__ == "__main__":
	info("Hello", "World")
	time.sleep(0.5)
	info("Hello", "World")
	time.sleep(0.5)
	info("Hello", "World")
	time.sleep(0.5)
	info("Not Hello World !")
	time.sleep(0.5)
	info("Hello", "World")
	time.sleep(0.5)
	info("Hello", "World")

	# All remaining print functions
	debug("Hello", "World")
	suggestion("Hello", "World")
	progress("Hello", "World")
	warning("Hello", "World")
	error("Hello", "World", exit=False)
	whatisit("Hello", "World")

