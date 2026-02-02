"""
This module provides utility functions for printing messages with different levels of importance.

If a message is printed multiple times, it will be displayed as "(xN) message"
where N is the number of times the message has been printed.

The module also includes a `colored()` function that formats text with Python 3.14 style coloring
for file paths, line numbers, function names (in magenta), and exception names (in bold magenta).
All functions have their colored counterparts with a 'c' suffix (e.g., `infoc()`, `debugc()`, etc.)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/print_module.gif
  :alt: stouputils print examples
"""

# Imports
import os
import sys
import time
from collections.abc import Callable, Iterable, Iterator
from typing import IO, Any, TextIO, cast

# Colors constants
RESET: str   = "\033[0m"
RED: str     = "\033[91m"
GREEN: str   = "\033[92m"
YELLOW: str  = "\033[93m"
BLUE: str    = "\033[94m"
MAGENTA: str = "\033[95m"
CYAN: str    = "\033[96m"
LINE_UP: str = "\033[1A"
BOLD: str    = "\033[1m"

# Constants
BAR_FORMAT: str = "{l_bar}{bar}" + MAGENTA + "| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}, {elapsed}<{remaining}]" + RESET

# Enable colors on Windows 10 terminal if applicable
if os.name == "nt":
	import subprocess
	subprocess.run("color", shell=True)

# Print functions
previous_args_kwards: tuple[Any, Any] = ((), {})
nb_values: int = 1
import_time: float = time.time()

# Colored for loop function
def colored_for_loop[T](
	iterable: Iterable[T],
	desc: str = "Processing",
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
	smooth_tqdm: bool = True,
	**kwargs: Any
) -> Iterator[T]:
	""" Function to iterate over a list with a colored TQDM progress bar like the other functions in this module.

	Args:
		iterable	(Iterable):			List to iterate over
		desc		(str):				Description of the function execution displayed in the progress bar
		color		(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format	(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii		(bool):				Whether to use ASCII or Unicode characters for the progress bar (Defaults to False)
		smooth_tqdm	(bool):				Whether to enable smooth progress bar updates by setting miniters=1 and mininterval=0.0 (Defaults to True)
		**kwargs:						Additional arguments to pass to the TQDM progress bar

	Yields:
		T: Each item of the iterable

	Examples:
		>>> for i in colored_for_loop(range(10), desc="Time sleeping loop"):
		...     time.sleep(0.01)
		>>> # Time sleeping loop: 100%|██████████████████| 10/10 [ 95.72it/s, 00:00<00:00]
	"""
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)
	desc = color + desc

	if smooth_tqdm:
		kwargs.setdefault("mininterval", 0.0)
		try:
			total = len(iterable) # type: ignore
			import shutil
			width = shutil.get_terminal_size().columns
			kwargs.setdefault("miniters", max(1, total // width))
		except (TypeError, OSError):
			kwargs.setdefault("miniters", 1)

	from tqdm.auto import tqdm
	yield from tqdm(iterable, desc=desc, bar_format=bar_format, ascii=ascii, **kwargs)

def format_colored(*values: Any) -> str:
	""" Format text with Python 3.14 style colored formatting.

	Dynamically colors text by analyzing each word:
	- File paths in magenta
	- Numbers in magenta
	- Function names (built-in and callable objects) in magenta
	- Exception names in bold magenta

	Args:
		values	(Any):	Values to format (like the print function)

	Returns:
		str: The formatted text with ANSI color codes

	Examples:
		>>> # Test function names with parentheses
		>>> result = format_colored("Call print() with 42 items")
		>>> result.count(MAGENTA)  # print and 42
		2

		>>> # Test function names without parentheses
		>>> result = format_colored("Use len and sum functions")
		>>> result.count(MAGENTA)  # len and sum
		2

		>>> # Test exceptions (bold magenta)
		>>> result = format_colored("Got ValueError when parsing")
		>>> result.count(MAGENTA), result.count(BOLD)  # ValueError in bold magenta
		(1, 1)

		>>> # Test file paths
		>>> result = format_colored("Processing ./data.csv file")
		>>> result.count(MAGENTA)  # ./data.csv
		1

		>>> # Test file paths with quotes
		>>> result = format_colored('File "/path/to/script.py" line 42')
		>>> result.count(MAGENTA)  # /path/to/script.py and 42
		2

		>>> # Test numbers
		>>> result = format_colored("Found 100 items and 3.14 value, 3.0e+10 is big")
		>>> result.count(MAGENTA)  # 100 and 3.14
		3

		>>> # Test mixed content
		>>> result = format_colored("Call sum() got IndexError at line 256 in utils.py")
		>>> result.count(MAGENTA)  # sum, IndexError (bold), and 256
		3
		>>> result.count(BOLD)  # IndexError is bold
		1

		>>> # Test keywords always colored
		>>> result = format_colored("Check class dtype type")
		>>> result.count(MAGENTA)  # class, dtype, type
		3

		>>> # Test plain text (no coloring)
		>>> result = format_colored("This is plain text")
		>>> result.count(MAGENTA) == 0 and result == "This is plain text"
		True

		>>> # Affix punctuation should not be colored (assert exact coloring, punctuation uncolored)
		>>> result = format_colored("<class")
		>>> result == "<" + MAGENTA + "class" + RESET
		True
		>>> result = format_colored("(dtype:")
		>>> result == "(" + MAGENTA + "dtype" + RESET + ":"
		True
		>>> result = format_colored("[1.")
		>>> result == "[" + MAGENTA + "1" + RESET + "."
		True

		>>> # Test complex
		>>> text = "<class 'numpy.ndarray'>, <id 140357548266896>: (dtype: float32, shape: (6,), min: 0.0, max: 1.0) [1. 0. 0. 0. 1. 0.]"
		>>> result = format_colored(text)
		>>> result.count(MAGENTA)  # class, numpy, ndarray, float32, 6, 0.0, 1.0, 1. 0.
		16
	"""
	import builtins
	import re

	# Dynamically retrieve all Python exception names and function names
	EXCEPTION_NAMES: set[str] = {
		name for name in dir(builtins)
		if isinstance(getattr(builtins, name, None), type)
		and issubclass(getattr(builtins, name), BaseException)
	}
	BUILTIN_FUNCTIONS: set[str] = {
		name for name in dir(builtins)
		if callable(getattr(builtins, name, None))
		and not (isinstance(getattr(builtins, name, None), type)
			and issubclass(getattr(builtins, name), BaseException))
	}

	# Additional keywords always colored (case-insensitive on stripped words)
	KEYWORDS: set[str] = {"class", "dtype", "type"}

	def is_filepath(word: str) -> bool:
		""" Check if a word looks like a file path """
		# Remove quotes if present
		clean_word: str = word.strip('"\'')

		# Check for path separators and file extensions
		if ('/' in clean_word or '\\' in clean_word) and '.' in clean_word:
			# Check if it has a reasonable extension (2-4 chars)
			parts = clean_word.split('.')
			if len(parts) >= 2 and 2 <= len(parts[-1]) <= 4:
				return True

		# Check for Windows absolute paths (C:\, D:\, etc.)
		if len(clean_word) > 3 and clean_word[1:3] == ':\\':
			return True

		# Check for Unix absolute paths starting with /
		if clean_word.startswith('/') and '.' in clean_word:
			return True

		return False

	def is_number(word: str) -> bool:
		try:
			float(''.join(c for c in word if c.isdigit() or c in '.-+e'))
			return True
		except ValueError:
			return False

	def is_function_name(word: str) -> tuple[bool, str]:
		# Check if word ends with () or just (, or it's a known built-in function
		clean_word: str = word.rstrip('.,;:!?')
		if clean_word.endswith(('()','(')) or clean_word in BUILTIN_FUNCTIONS:
			return (True, clean_word)
		return (False, "")

	def is_exception(word: str) -> bool:
		""" Check if a word is a known exception name """
		return ''.join(c for c in word if c.isalnum()) in EXCEPTION_NAMES

	def is_keyword(word: str) -> bool:
		""" Check if a word is one of the always-colored keywords """
		clean_alnum = ''.join(c for c in word if c.isalnum())
		return clean_alnum in KEYWORDS

	def split_affixes(w: str) -> tuple[str, str, str]:
		""" Split leading/trailing non-word characters and return (prefix, core, suffix).

		This preserves punctuation like '<', '(', '[', '"', etc., while operating on the core text.
		"""
		m = re.match(r'^(\W*)(.*?)(\W*)$', w, re.ASCII)
		if m:
			return m.group(1), m.group(2), m.group(3)
		return "", w, ""

	# Convert all values to strings and join them and split into words while preserving separators
	text: str = " ".join(str(v) for v in values)
	words: list[str] = re.split(r'(\s+)', text)

	# Process each word
	colored_words: list[str] = []
	i: int = 0
	while i < len(words):
		word = words[i]

		# Skip whitespace
		if word.isspace():
			colored_words.append(word)
			i += 1
			continue

		# If the whole token looks like a filepath (e.g. './data.csv' or '/path/to/file'), color it as-is
		colored: bool = False
		if is_filepath(word):
			colored_words.append(f"{MAGENTA}{word}{RESET}")
			colored = True
		else:
			# Split affixes to preserve punctuation like '<', '(', '[' etc.
			prefix, core, suffix = split_affixes(word)

			# Try to identify and color the word (operate on core where applicable)
			if is_filepath(core):
				colored_words.append(f"{prefix}{MAGENTA}{core}{RESET}{suffix}")
				colored = True
			elif is_exception(core):
				colored_words.append(f"{prefix}{BOLD}{MAGENTA}{core}{RESET}{suffix}")
				colored = True
			elif is_number(core):
				colored_words.append(f"{prefix}{MAGENTA}{core}{RESET}{suffix}")
				colored = True
			elif is_keyword(core):
				colored_words.append(f"{prefix}{MAGENTA}{core}{RESET}{suffix}")
				colored = True
			elif is_function_name(core)[0]:
				func_name = is_function_name(core)[1]
				# Find where the function name ends in the core
				func_start = core.find(func_name)
				if func_start != -1:
					pre_core = core[:func_start]
					func_end = func_start + len(func_name)
					post_core = core[func_end:]
					colored_words.append(f"{prefix}{pre_core}{MAGENTA}{func_name}{RESET}{post_core}{suffix}")
				else:
					# Fallback if we can't find it (shouldn't happen)
					colored_words.append(f"{prefix}{MAGENTA}{core}{RESET}{suffix}")
				colored = True

		# If nothing matched, keep the original word
		if not colored:
			colored_words.append(word)
		i += 1

	# Join and return
	return "".join(colored_words)

def colored(
	*values: Any,
	file: TextIO | None = None,
	**print_kwargs: Any,
) -> None:
	""" Print with Python 3.14 style colored formatting.

	Dynamically colors text by analyzing each word:
	- File paths in magenta
	- Numbers in magenta
	- Function names (built-in and callable objects) in magenta
	- Exception names in bold magenta

	Args:
		values			(Any):		Values to print (like the print function)
		file			(TextIO):	File to write the message to (default: sys.stdout)
		print_kwargs	(dict):		Keyword arguments to pass to the print function

	Examples:
		>>> colored("File '/path/to/file.py', line 42, in function_name")  # doctest: +SKIP
		>>> colored("KeyboardInterrupt")  # doctest: +SKIP
		>>> colored("Processing data.csv with 100 items")  # doctest: +SKIP
		>>> colored("Using print and len functions")  # doctest: +SKIP
	"""
	if file is None:
		file = sys.stdout

	result: str = format_colored(*values)
	print(result, file=file, **print_kwargs)

def info(
	*values: Any,
	color: str = GREEN,
	text: str = "INFO ",
	prefix: str = "",
	file: TextIO | list[TextIO] | None = None,
	use_colored: bool = False,
	**print_kwargs: Any,
) -> None:
	""" Print an information message looking like "[INFO HH:MM:SS] message" in green by default.

	Args:
		values			(Any):					Values to print (like the print function)
		color			(str):					Color of the message (default: GREEN)
		text			(str):					Text of the message (default: "INFO ")
		prefix			(str):					Prefix to add to the values
		file			(TextIO|list[TextIO]):	File(s) to write the message to (default: sys.stdout)
		use_colored		(bool):					Whether to use the colored() function to format the message
		print_kwargs	(dict):					Keyword arguments to pass to the print function
	"""
	# Use stdout if no file is specified
	if file is None:
		file = sys.stdout

	# If file is a list, recursively call info() for each file
	if isinstance(file, list):
		for f in file:
			info(*values, color=color, text=text, prefix=prefix, file=f, use_colored=use_colored, **print_kwargs)
	else:
		# Build the message with prefix, color, text and timestamp
		message: str = f"{prefix}{color}[{text} {current_time()}]"

		# If this is a repeated print, add a line up and counter
		if is_same_print(*values, color=color, text=text, prefix=prefix, **print_kwargs):
			message = f"{LINE_UP}{message} (x{nb_values})"

		# Print the message with the values and reset color
		if use_colored:
			print(message, format_colored(*values).replace(RESET, RESET+color), RESET, file=file, **print_kwargs)
		else:
			print(message, *values, RESET, file=file, **print_kwargs)

def debug(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" in cyan by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "DEBUG"
	if "color" not in print_kwargs:
		print_kwargs["color"] = CYAN
	info(*values, flush=flush, **print_kwargs)

def alt_debug(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" in blue by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "DEBUG"
	if "color" not in print_kwargs:
		print_kwargs["color"] = BLUE
	info(*values, flush=flush, **print_kwargs)

def suggestion(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
	""" Print a suggestion message looking like "[SUGGESTION HH:MM:SS] message" in cyan by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "SUGGESTION"
	if "color" not in print_kwargs:
		print_kwargs["color"] = CYAN
	info(*values, flush=flush, **print_kwargs)

def progress(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
	""" Print a progress message looking like "[PROGRESS HH:MM:SS] message" in magenta by default. """
	if "text" not in print_kwargs:
		print_kwargs["text"] = "PROGRESS"
	if "color" not in print_kwargs:
		print_kwargs["color"] = MAGENTA
	info(*values, flush=flush, **print_kwargs)

def warning(*values: Any, flush: bool = True, **print_kwargs: Any) -> None:
	""" Print a warning message looking like "[WARNING HH:MM:SS] message" in yellow by default and in sys.stderr. """
	if "file" not in print_kwargs:
		print_kwargs["file"] = sys.stderr
	if "text" not in print_kwargs:
		print_kwargs["text"] = "WARNING"
	if "color" not in print_kwargs:
		print_kwargs["color"] = YELLOW
	info(*values, flush=flush, **print_kwargs)

def error(*values: Any, exit: bool = False, flush: bool = True, **print_kwargs: Any) -> None:
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
	info(*values, flush=flush, **print_kwargs)
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
	flush: bool = True,
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

	# Add the color to the message
	if "color" not in print_kwargs:
		print_kwargs["color"] = color

	# Set text to "What is it?" if not already set
	if "text" not in print_kwargs:
		print_kwargs["text"] = "What is it?"

	# Print the values
	if len(values) > 1:
		print_function("".join(f"\n  {_internal(value)}" for value in values), flush=flush, **print_kwargs)
	elif len(values) == 1:
		print_function(_internal(values[0]), flush=flush, **print_kwargs)

def breakpoint(*values: Any, print_function: Callable[..., None] = warning, flush: bool = True, **print_kwargs: Any) -> None:
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
	whatisit(*values, print_function=print_function, flush=flush, **print_kwargs)
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

# Convenience colored functions
def infoc(*args: Any, **kwargs: Any) -> None:
	return info(*args, use_colored=True, **kwargs)
def debugc(*args: Any, **kwargs: Any) -> None:
	return debug(*args, use_colored=True, **kwargs)
def alt_debugc(*args: Any, **kwargs: Any) -> None:
	return alt_debug(*args, use_colored=True, **kwargs)
def warningc(*args: Any, **kwargs: Any) -> None:
	return warning(*args, use_colored=True, **kwargs)
def errorc(*args: Any, **kwargs: Any) -> None:
	return error(*args, use_colored=True, **kwargs)
def progressc(*args: Any, **kwargs: Any) -> None:
	return progress(*args, use_colored=True, **kwargs)
def suggestionc(*args: Any, **kwargs: Any) -> None:
	return suggestion(*args, use_colored=True, **kwargs)
def whatisitc(*args: Any, **kwargs: Any) -> None:
	return whatisit(*args, use_colored=True, **kwargs)
def breakpointc(*args: Any, **kwargs: Any) -> None:
	return breakpoint(*args, use_colored=True, **kwargs)


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

