"""
This module provides utility functions for printing messages with different levels of importance.

If a message is printed multiple times, it will be displayed as "(xN) message"
where N is the number of times the message has been printed.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/print_module.gif
  :alt: stouputils print examples
"""

# Imports
import os
import sys
import time
from collections.abc import Callable
from typing import IO, Any, TextIO

# Colors constants
RESET: str   = "\033[0m"
RED: str     = "\033[91m"
GREEN: str   = "\033[92m"
YELLOW: str  = "\033[93m"
BLUE: str    = "\033[94m"
MAGENTA: str = "\033[95m"
CYAN: str    = "\033[96m"
LINE_UP: str = "\033[1A"

# Enable colors on Windows 10 terminal if applicable
if os.name == "nt":
	os.system("color")

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

def info(
	*values: Any,
	color: str = GREEN,
	text: str = "INFO ",
	prefix: str = "",
	file: TextIO | list[TextIO] | None = None,
	**print_kwargs: Any,
) -> None:
	""" Print an information message looking like "[INFO HH:MM:SS] message" in green by default.

	Args:
		values			(Any):					Values to print (like the print function)
		color			(str):					Color of the message (default: GREEN)
		text			(str):					Text of the message (default: "INFO ")
		prefix			(str):					Prefix to add to the values
		file			(TextIO|list[TextIO]):	File(s) to write the message to (default: sys.stdout)
		print_kwargs	(dict):					Keyword arguments to pass to the print function
	"""
	# Use stdout if no file is specified
	if file is None:
		file = sys.stdout

	# If file is a list, recursively call info() for each file
	if isinstance(file, list):
		for f in file:
			info(*values, color=color, text=text, prefix=prefix, file=f, **print_kwargs)
	else:
		# Build the message with prefix, color, text and timestamp
		message: str = f"{prefix}{color}[{text} {current_time()}]"

		# If this is a repeated print, add a line up and counter
		if is_same_print(*values, color=color, text=text, prefix=prefix, **print_kwargs):
			message = f"{LINE_UP}{message} (x{nb_values})"

		# Print the message with the values and reset color
		print(message, *values, RESET, file=file, **print_kwargs)

def debug(*values: Any, **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" in cyan by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "DEBUG"
	if "color" not in print_kwargs:
		print_kwargs["color"] = CYAN
	info(*values, **print_kwargs)

def alt_debug(*values: Any, **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" in blue by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "DEBUG"
	if "color" not in print_kwargs:
		print_kwargs["color"] = BLUE
	info(*values, **print_kwargs)

def suggestion(*values: Any, **print_kwargs: Any) -> None:
	""" Print a suggestion message looking like "[SUGGESTION HH:MM:SS] message" in cyan by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "SUGGESTION"
	if "color" not in print_kwargs:
		print_kwargs["color"] = CYAN
	info(*values, **print_kwargs)

def progress(*values: Any, **print_kwargs: Any) -> None:
	""" Print a progress message looking like "[PROGRESS HH:MM:SS] message" in magenta by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "PROGRESS"
	if "color" not in print_kwargs:
		print_kwargs["color"] = MAGENTA
	info(*values, **print_kwargs)

def warning(*values: Any, **print_kwargs: Any) -> None:
	""" Print a warning message looking like "[WARNING HH:MM:SS] message" in yellow by default and in sys.stderr. """
	if "file" not in print_kwargs:
		print_kwargs["file"] = sys.stderr
	if "text" not in print_kwargs:
		print_kwargs["text"] = "WARNING"
	if "color" not in print_kwargs:
		print_kwargs["color"] = YELLOW
	info(*values, **print_kwargs)

def error(*values: Any, exit: bool = True, **print_kwargs: Any) -> None:
	""" Print an error message (in sys.stderr and in red by default)
	and optionally ask the user to continue or stop the program.

	Args:
		values			(Any):		Values to print (like the print function)
		exit			(bool):		Whether to ask the user to continue or stop the program,
			false to ignore the error automatically and continue
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

def whatisit(
	*values: Any,
	print_function: Callable[..., None] = debug,
	max_length: int = 250,
	color: str = CYAN,
	**print_kwargs: Any,
) -> None:
	""" Print the type of each value and the value itself, with its id and length/shape.

	The output format is: "type, <id id_number>:	(length/shape) value"

	Args:
		values			(Any):		Values to print
		print_function	(Callable):	Function to use to print the values (default: debug())
		max_length		(int):		Maximum length of the value string to print (default: 250)
		color			(str):		Color of the message (default: CYAN)
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	def _internal(value: Any) -> str:
		""" Get the string representation of the value, with length or shape instead of length if shape is available """

		# Get the length or shape of the value
		length: str = ""
		try:
			length = f"(length: {len(value)}) "
		except (AttributeError, TypeError):
			pass
		try:
			length = f"(shape: {value.shape}) "
		except (AttributeError, TypeError):
			pass

		# Get the string representation of the value
		value_str: str = str(value)
		if len(value_str) > max_length:
			value_str = value_str[:max_length] + "..."
		if "\n" in value_str:
			value_str = "\n" + value_str	# Add a newline before the value if there is a newline in it.

		# Return the formatted string
		return f"{type(value)}, <id {id(value)}>: {length}{value_str}"

	# Add the color to the message
	if "color" not in print_kwargs:
		print_kwargs["color"] = color

	# Print the values
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


# TeeMultiOutput class to duplicate output to multiple file-like objects
class TeeMultiOutput:
	""" File-like object that duplicates output to multiple file-like objects.

	Args:
		*files         (IO[Any]):  One or more file-like objects that have write and flush methods
		strip_colors   (bool):     Strip ANSI color codes from output sent to non-stdout/stderr files
		ascii_only     (bool):     Replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files
		ignore_lineup  (bool):     Ignore lines containing LINE_UP escape sequence in non-terminal outputs

	Examples:
		>>> f = open("logfile.txt", "w")
		>>> original_stdout = sys.stdout
		>>> sys.stdout = TeeMultiOutput(sys.stdout, f)
		>>> print("Hello World")  # Output goes to both console and file
		Hello World
		>>> sys.stdout = original_stdout
		>>> f.close()
	"""
	def __init__(
		self, *files: IO[Any], strip_colors: bool = True, ascii_only: bool = True, ignore_lineup: bool = True
	) -> None:
		self.files: tuple[IO[Any], ...] = files
		""" File-like objects to write to """
		self.strip_colors: bool = strip_colors
		""" Whether to strip ANSI color codes from output sent to non-stdout/stderr files """
		self.ascii_only: bool = ascii_only
		""" Whether to replace non-ASCII characters with their ASCII equivalents for non-stdout/stderr files """
		self.ignore_lineup: bool = ignore_lineup
		""" Whether to ignore lines containing LINE_UP escape sequence in non-terminal outputs """

	@property
	def encoding(self) -> str:
		""" Get the encoding of the first file, or "utf-8" as fallback.

		Returns:
			str: The encoding, ex: "utf-8", "ascii", "latin1", etc.
		"""
		try:
			return self.files[0].encoding	# type: ignore
		except (IndexError, AttributeError):
			return "utf-8"

	def write(self, obj: str) -> None:
		""" Write the object to all files while stripping colors if needed.

		Args:
			obj (str): String to write
		"""
		for i, f in enumerate(self.files):
			try:
				content = obj
				if i != 0:
					# First file (i = 0) (often stdout/stderr) gets the original content
					# Other files (i != 0) get processed content

					# Skip content if it contains LINE_UP and ignore_lineup is True
					if self.ignore_lineup and (LINE_UP in content or "\r" in content):
						continue

					# Strip colors if needed
					if self.strip_colors:
						content = remove_colors(content)

					# Replace Unicode block characters with ASCII equivalents
					# Replace other problematic Unicode characters as needed
					if self.ascii_only:
						content = content.replace('█', '#')
						content = ''.join(c if ord(c) < 128 else '?' for c in content)

				# Write content to file
				f.write(content)

			except Exception:
				pass

	def flush(self) -> None:
		""" Flush all files. """
		for f in self.files:
			try:
				f.flush()
			except Exception:
				pass

	def fileno(self) -> int:
		""" Return the file descriptor of the first file. """
		return self.files[0].fileno() if hasattr(self.files[0], "fileno") else 0



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

