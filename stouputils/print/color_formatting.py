
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import sys
from typing import Any, TextIO

from ..config import StouputilsConfig as Cfg
from .colorizer import WordColorizer


def format_colored(*values: Any, color: str = Cfg.MAGENTA) -> str:
	""" Format text with Python 3.14 style colored formatting.

	Dynamically colors text by analyzing each word:
	- File paths in the specified color
	- Numbers in the specified color
	- Function names (built-in and callable objects) in the specified color
	- Exception names in bold with the specified color

	Args:
		values: Values to format (like the print function)
		color:  ANSI color code to use for coloring (default: Cfg.MAGENTA)
	Returns:
		The formatted text with ANSI color codes
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
		>>> result = format_colored("This is not a path: batches/images")
		>>> result == "This is not a path: batches/images"
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
	return WordColorizer(color=color).colorize_text(" ".join(str(value) for value in values))

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
		values:       Values to print (like the print function)
		file:         File to write the message to (default: sys.stdout)
		print_kwargs: Keyword arguments to pass to the print function
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

