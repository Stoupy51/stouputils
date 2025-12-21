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
from collections.abc import Callable, Iterable, Iterator
from typing import IO, Any, TextIO, TypeVar, cast

# Colors constants
RESET: str   = "\033[0m"
RED: str     = "\033[91m"
GREEN: str   = "\033[92m"
YELLOW: str  = "\033[93m"
BLUE: str    = "\033[94m"
MAGENTA: str = "\033[95m"
CYAN: str    = "\033[96m"
LINE_UP: str = "\033[1A"

# Constants
BAR_FORMAT: str = "{l_bar}{bar}" + MAGENTA + "| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}, {elapsed}<{remaining}]" + RESET
T = TypeVar("T")

# Enable colors on Windows 10 terminal if applicable
if os.name == "nt":
	os.system("color")

# Print functions
previous_args_kwards: tuple[Any, Any] = ((), {})
nb_values: int = 1
import_time: float = time.time()

# Colored for loop function
def colored_for_loop(
	iterable: Iterable[T],
	desc: str = "Processing",
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
	**kwargs: Any
) -> Iterator[T]:
	""" Function to iterate over a list with a colored TQDM progress bar like the other functions in this module.

	Args:
		iterable	(Iterable):			List to iterate over
		desc		(str):				Description of the function execution displayed in the progress bar
		color		(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format	(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii		(bool):				Whether to use ASCII or Unicode characters for the progress bar (Defaults to False)
		verbose		(int):				Level of verbosity, decrease by 1 for each depth (Defaults to 1)
		**kwargs:						Additional arguments to pass to the TQDM progress bar

	Yields:
		T:		Each item of the iterable

	Examples:
		>>> for i in colored_for_loop(range(10), desc="Time sleeping loop"):
		...     time.sleep(0.01)
		>>> # Time sleeping loop: 100%|██████████████████| 10/10 [ 95.72it/s, 00:00<00:00]
	"""
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)
	desc = color + desc

	from tqdm.auto import tqdm
	yield from tqdm(iterable, desc=desc, bar_format=bar_format, ascii=ascii, **kwargs)

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

def error(*values: Any, exit: bool = False, **print_kwargs: Any) -> None:
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
			file = cast(TextIO, print_kwargs["file"][0])
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

		# Build metadata parts list
		metadata_parts: list[str] = []

		# Get the dtype if available
		try:
			metadata_parts.append(f"dtype: {value.dtype}")
		except (AttributeError, TypeError):
			pass

		# Get the shape or length of the value
		try:
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
				metadata_parts.append(f"min: {np.min(value)}")
				metadata_parts.append(f"max: {np.max(value)}")
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

	# Add the color to the message
	if "color" not in print_kwargs:
		print_kwargs["color"] = color

	# Set text to "What is it?" if not already set
	if "text" not in print_kwargs:
		print_kwargs["text"] = "What is it?"

	# Print the values
	if len(values) > 1:
		print_function("".join(f"\n  {_internal(value)}" for value in values), **print_kwargs)
	elif len(values) == 1:
		print_function(_internal(values[0]), **print_kwargs)

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
			file = cast(TextIO, print_kwargs["file"][0])
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
		>>> sys.stdout = TeeMultiOutput(sys.stdout, f)
		>>> print("Hello World")  # Output goes to both console and file
		Hello World
		>>> f.close()	# TeeMultiOutput will handle any future writes to closed files gracefully
	"""
	def __init__(
		self, *files: IO[Any], strip_colors: bool = True, ascii_only: bool = True, ignore_lineup: bool = True
	) -> None:
		# Flatten any TeeMultiOutput instances in files
		flattened_files: list[IO[Any]] = []
		for file in files:
			if isinstance(file, TeeMultiOutput):
				flattened_files.extend(file.files)
			else:
				flattened_files.append(file)

		self.files: tuple[IO[Any], ...] = tuple(flattened_files)
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

	def write(self, obj: str) -> int:
		""" Write the object to all files while stripping colors if needed.

		Args:
			obj (str): String to write
		Returns:
			int: Number of characters written to the first file
		"""
		files_to_remove: list[IO[Any]] = []
		num_chars_written: int = 0
		for i, f in enumerate(self.files):
			try:
				# Check if file is closed
				if hasattr(f, "closed") and f.closed:
					files_to_remove.append(f)
					continue

				# Check if this file is a terminal/console or a regular file
				content: str = obj
				if not (hasattr(f, "isatty") and f.isatty()):
					# Non-terminal files get processed content (stripped colors, ASCII-only, etc.)

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
				if i == 0:
					num_chars_written = f.write(content)
				else:
					f.write(content)

			except ValueError:
				# ValueError is raised when writing to a closed file
				files_to_remove.append(f)
			except Exception:
				pass

		# Remove closed files from the list
		if files_to_remove:
			self.files = tuple(f for f in self.files if f not in files_to_remove)
		return num_chars_written

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


# Utility functions
def remove_colors(text: str) -> str:
	""" Remove the colors from a text """
	for color in [RESET, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, LINE_UP]:
		text = text.replace(color, "")
	return text

def is_same_print(*args: Any, **kwargs: Any) -> bool:
	""" Checks if the current print call is the same as the previous one. """
	global previous_args_kwards, nb_values
	try:
		if previous_args_kwards == (args, kwargs):
			nb_values += 1
			return True
	except Exception:
		# Comparison failed (e.g., comparing DataFrames or other complex objects)
		# Use str() for comparison instead
		current_str: str = str((args, kwargs))
		previous_str: str = str(previous_args_kwards)
		if previous_str == current_str:
			nb_values += 1
			return True
	# Else, update previous args and reset counter
	previous_args_kwards = (args, kwargs)
	nb_values = 1
	return False

def current_time() -> str:
	""" Get the current time as "HH:MM:SS" if less than 24 hours since import, else "YYYY-MM-DD HH:MM:SS" """
	# If the import time is more than 24 hours, return the full datetime
	if (time.time() - import_time) > (24 * 60 * 60):
		return time.strftime("%Y-%m-%d %H:%M:%S")
	else:
		return time.strftime("%H:%M:%S")


def show_version(main_package: str = "stouputils", primary_color: str = CYAN, secondary_color: str = GREEN) -> None:
	""" Print the version of the main package and its dependencies.

	Used by the "stouputils --version" command.

	Args:
		main_package			(str):			Name of the main package to show version for
		primary_color			(str):			Color to use for the primary package name
		secondary_color			(str):			Color to use for the secondary package names
	"""
	# Imports
	from importlib.metadata import requires, version
	def ver(package_name: str) -> str:
		try:
			return version(package_name)
		except Exception:
			return ""

	# Get dependencies dynamically and extract package names from requirements (e.g., "tqdm>=4.0.0" -> "tqdm")
	deps: list[str] = requires(main_package) or []
	dep_names: list[str] = sorted([
		dep
			.split(">")[0]
			.split("<")[0]
			.split("=")[0]
			.split("[")[0]
		for dep in deps
	])
	all_deps: list[tuple[str, str]] = [
		(x, ver(x).split("version: ")[-1])
		for x in (main_package, *dep_names)
	]
	all_deps = [pair for pair in all_deps if pair[1]]  # Filter out packages with no version found
	longest_name_length: int = max(len(name) for name, _ in all_deps)
	longest_version_length: int = max(len(ver) for _, ver in all_deps)

	# Get Python version
	python_version: str = f" Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} "
	minimum_separator_length: int = len(python_version) + 10	# Always at least 5 dashes on each side
	separator_length: int = max(minimum_separator_length, longest_name_length + longest_version_length + 4)
	python_text_length: int = len(python_version)
	left_dashes: int = (separator_length - python_text_length) // 2
	right_dashes: int = separator_length - python_text_length - left_dashes
	separator_with_python: str = "─" * left_dashes + python_version + "─" * right_dashes
	separator: str = "─" * separator_length

	for pkg, v in all_deps:
		pkg_spacing: str = " " * (longest_name_length - len(pkg))

		# Highlight the main package with a different style
		if pkg == main_package:
			print(f"{primary_color}{separator_with_python}{RESET}")
			print(f"{primary_color}{pkg}{pkg_spacing}  {secondary_color}v{v}{RESET}")
			print(f"{primary_color}{separator}{RESET}")
		else:
			print(f"{primary_color}{pkg}{pkg_spacing}  {secondary_color}v{v}{RESET}")
	return

# Test the print functions
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
	alt_debug("Hello", "World")
	debug("Hello", "World")
	suggestion("Hello", "World")
	progress("Hello", "World")
	warning("Hello", "World")
	error("Hello", "World", exit=False)
	whatisit("Hello")
	whatisit("Hello", "World")

	# Test whatisit with different types
	import numpy as np
	print()
	whatisit(
		123,
		"Hello World",
		[1, 2, 3, 4, 5],
		np.array([[1, 2, 3], [4, 5, 6]]),
		{"a": 1, "b": 2},
	)

