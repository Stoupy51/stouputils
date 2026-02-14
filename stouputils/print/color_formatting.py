
# Imports
import sys
from typing import Any, TextIO

from ..config import StouputilsConfig as Cfg


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
		>>> result.count(Cfg.MAGENTA)  # print and 42
		2

		>>> # Test function names without parentheses
		>>> result = format_colored("Use len and sum functions")
		>>> result.count(Cfg.MAGENTA)  # len and sum
		2

		>>> # Test exceptions (bold magenta)
		>>> result = format_colored("Got ValueError when parsing")
		>>> result.count(Cfg.MAGENTA), result.count(Cfg.BOLD)  # ValueError in bold magenta
		(1, 1)

		>>> # Test file paths
		>>> result = format_colored("Processing ./data.csv file")
		>>> result.count(Cfg.MAGENTA)  # ./data.csv
		1

		>>> # Test file paths with quotes
		>>> result = format_colored('File "/path/to/script.py" line 42')
		>>> result.count(Cfg.MAGENTA)  # /path/to/script.py and 42
		2

		>>> # Test numbers
		>>> result = format_colored("Found 100 items and 3.14 value, 3.0e+10 is big")
		>>> result.count(Cfg.MAGENTA)  # 100 and 3.14
		3

		>>> # Test mixed content
		>>> result = format_colored("Call sum() got IndexError at line 256 in utils.py")
		>>> result.count(Cfg.MAGENTA)  # sum, IndexError (bold), and 256
		3
		>>> result.count(Cfg.BOLD)  # IndexError is bold
		1

		>>> # Test keywords always colored
		>>> result = format_colored("Check class dtype type")
		>>> result.count(Cfg.MAGENTA)  # class, dtype, type
		3

		>>> # Test plain text (no coloring)
		>>> result = format_colored("This is plain text")
		>>> result.count(Cfg.MAGENTA) == 0 and result == "This is plain text"
		True

		>>> # Affix punctuation should not be colored (assert exact coloring, punctuation uncolored)
		>>> result = format_colored("<class")
		>>> result == "<" + Cfg.MAGENTA + "class" + Cfg.RESET
		True
		>>> result = format_colored("(dtype:")
		>>> result == "(" + Cfg.MAGENTA + "dtype" + Cfg.RESET + ":"
		True
		>>> result = format_colored("[1.")
		>>> result == "[" + Cfg.MAGENTA + "1" + Cfg.RESET + "."
		True

		>>> # Test complex
		>>> text = "<class 'numpy.ndarray'>, <id 140357548266896>: (dtype: float32, shape: (6,), min: 0.0, max: 1.0) [1. 0. 0. 0. 1. 0.]"
		>>> result = format_colored(text)
		>>> result.count(Cfg.MAGENTA)  # class, numpy, ndarray, float32, 6, 0.0, 1.0, 1. 0.
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
			colored_words.append(f"{Cfg.MAGENTA}{word}{Cfg.RESET}")
			colored = True
		else:
			# Split affixes to preserve punctuation like '<', '(', '[' etc.
			prefix, core, suffix = split_affixes(word)

			# Try to identify and color the word (operate on core where applicable)
			if is_filepath(core):
				colored_words.append(f"{prefix}{Cfg.MAGENTA}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_exception(core):
				colored_words.append(f"{prefix}{Cfg.BOLD}{Cfg.MAGENTA}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_number(core):
				colored_words.append(f"{prefix}{Cfg.MAGENTA}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_keyword(core):
				colored_words.append(f"{prefix}{Cfg.MAGENTA}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_function_name(core)[0]:
				func_name = is_function_name(core)[1]
				# Find where the function name ends in the core
				func_start = core.find(func_name)
				if func_start != -1:
					pre_core = core[:func_start]
					func_end = func_start + len(func_name)
					post_core = core[func_end:]
					colored_words.append(f"{prefix}{pre_core}{Cfg.MAGENTA}{func_name}{Cfg.RESET}{post_core}{suffix}")
				else:
					# Fallback if we can't find it (shouldn't happen)
					colored_words.append(f"{prefix}{Cfg.MAGENTA}{core}{Cfg.RESET}{suffix}")
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

