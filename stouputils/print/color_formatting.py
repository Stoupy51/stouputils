
# Imports
import sys
from typing import Any, TextIO

from ..config import StouputilsConfig as Cfg


def format_colored(*values: Any, color: str = Cfg.MAGENTA) -> str:
	""" Format text with Python 3.14 style colored formatting.

	Dynamically colors text by analyzing each word:
	- File paths in the specified color
	- Numbers in the specified color
	- Function names (built-in and callable objects) in the specified color
	- Exception names in bold with the specified color

	Args:
		values	(Any):	Values to format (like the print function)
		color	(str):	ANSI color code to use for coloring (default: Cfg.MAGENTA)

	Returns:
		str: The formatted text with ANSI color codes

	Examples:
		>>> # Test function names with parentheses
		>>> result = format_colored("Call print() with 42 items")
		>>> m, r, b = Cfg.MAGENTA, Cfg.RESET, Cfg.BOLD
		>>> result == f"Call {m}print{r}() with {m}42{r} items"
		True

		>>> # Test function names without parentheses
		>>> result = format_colored("Use len and sum functions")
		>>> result == f"Use {m}len{r} and {m}sum{r} functions"
		True

		>>> # Test exceptions (bold magenta)
		>>> result = format_colored("Got ValueError when parsing")
		>>> result == f"Got {b}{m}ValueError{r} when parsing"
		True

		>>> # Test file paths
		>>> result = format_colored("Processing ./data.csv file")
		>>> result == f"Processing {m}./data.csv{r} file"
		True
		>>> result = format_colored("Processing ./data/some/sub/directory")
		>>> result == f"Processing {m}./data/some/sub/directory{r}"
		True

		>>> # Test file paths with quotes
		>>> result = format_colored('File "/path/to/script.py" line 42')
		>>> result == f'File {m}"/path/to/script.py"{r} line {m}42{r}'
		True

		>>> # Test numbers
		>>> result = format_colored("Found 100 items and 3.14 value, 3.0e+10 is big")
		>>> result == f"Found {m}100{r} items and {m}3.14{r} value, {m}3.0e+10{r} is big"
		True

		>>> # Test numbers embedded in non-numeric tokens (both must be colored the same)
		>>> result = format_colored("scale=(0.5, 0.5), overlap=(0.0, 0.0)")
		>>> result == f"scale=({m}0.5{r}, {m}0.5{r}), overlap=({m}0.0{r}, {m}0.0{r})"
		True
		>>> result = format_colored("took: 2.885ms")
		>>> result == f"took: {m}2.885{r}ms"
		True

		>>> # Test mixed content
		>>> result = format_colored("Call sum() got IndexError at line 256 in utils.py")
		>>> result == f"Call {m}sum{r}() got {b}{m}IndexError{r} at line {m}256{r} in utils.py"
		True

		>>> # Test keywords always colored
		>>> result = format_colored("Check class dtype type")
		>>> result == f"Check {m}class{r} {m}dtype{r} {m}type{r}"
		True

		>>> # Test plain text (no coloring)
		>>> result = format_colored("This is plain text")
		>>> result == "This is plain text"
		True

		>>> # Affix punctuation should not be colored (assert exact coloring, punctuation uncolored)
		>>> result = format_colored("<class")
		>>> result == f"<{m}class{r}"
		True
		>>> result = format_colored("(dtype:")
		>>> result == f"({m}dtype{r}:"
		True
		>>> result = format_colored("[1.")
		>>> result == f"[{m}1{r}."
		True

		>>> # Test complex
		>>> text = "<class 'numpy.ndarray'>, <id 14036>: (dtype: float32, shape: (6,), min: 0.0, max: 1.0) [1. 0. 0. 0. 1. 0.]"
		>>> result = format_colored(text)
		>>> result == f"<{m}class{r} {m}'numpy.ndarray'{r}>, <{m}id{r} {m}14036{r}>: ({m}dtype{r}: float{m}32{r}, shape: ({m}6{r},), {m}min{r}: {m}0.0{r}, {m}max{r}: {m}1.0{r}) [{m}1{r}. {m}0{r}. {m}0{r}. {m}0{r}. {m}1{r}. {m}0{r}.]"
		True
		>>> result = format_colored("Specimen: 'C-B250021834A02HES002-NH4': 24.29029s")
		>>> result == f"Specimen: {m}'C-B250021834A02HES002-NH4'{r}: {m}24.29029{r}s"
		True
	"""  # noqa: E501
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

		# Check for path separators (with or without file extension)
		if '/' in clean_word or '\\' in clean_word:

			# Has a file extension (2-4 chars after last dot)
			if '.' in clean_word:
				parts = clean_word.split('.')
				if len(parts) >= 2 and 2 <= len(parts[-1]) <= 4:
					return True

			# No extension but multiple path components (e.g. ./data/some/sub/directory)
			sep = '/' if '/' in clean_word else '\\'
			if len(clean_word.split(sep)) >= 2:
				return True

		# Check for Windows absolute paths (C:\, D:\, etc.)
		if len(clean_word) > 3 and clean_word[1:3] == ':\\':
			return True

		# Check for Unix absolute paths starting with /
		if clean_word.startswith('/'):
			return True

		return False

	def is_number(word: str) -> bool:
		try:
			float(word)
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
			colored_words.append(f"{color}{word}{Cfg.RESET}")
			colored = True
		elif qm := re.match(r"^(\W*?)('[^']*'|\"[^\"]*\")(\W*)$", word):
			# Quoted string token (e.g. "'C-B250021834A02HES002-NH4':") — color the quoted part
			colored_words.append(f"{qm.group(1)}{color}{qm.group(2)}{Cfg.RESET}{qm.group(3)}")
			colored = True
		else:
			# Split affixes to preserve punctuation like '<', '(', '[' etc.
			prefix, core, suffix = split_affixes(word)

			# Try to identify and color the word (operate on core where applicable)
			if is_filepath(core):
				colored_words.append(f"{prefix}{color}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_exception(core):
				colored_words.append(f"{prefix}{Cfg.BOLD}{color}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_number(core):
				colored_words.append(f"{prefix}{color}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_keyword(core):
				colored_words.append(f"{prefix}{color}{core}{Cfg.RESET}{suffix}")
				colored = True
			elif is_function_name(core)[0]:
				func_name = is_function_name(core)[1]
				# Find where the function name ends in the core
				func_start = core.find(func_name)
				if func_start != -1:
					pre_core = core[:func_start]
					func_end = func_start + len(func_name)
					post_core = core[func_end:]
					colored_words.append(f"{prefix}{pre_core}{color}{func_name}{Cfg.RESET}{post_core}{suffix}")
				else:
					# Fallback if we can't find it (shouldn't happen)
					colored_words.append(f"{prefix}{color}{core}{Cfg.RESET}{suffix}")
				colored = True

		# If nothing matched, try to color embedded numeric subpatterns (e.g. "scale=(0.5,")
		if not colored:
			new_word = re.sub(
				r'(\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)',
				lambda m: f"{color}{m.group()}{Cfg.RESET}",
				word
			)
			colored_words.append(new_word)
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

