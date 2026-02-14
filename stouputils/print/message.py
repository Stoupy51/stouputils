
# Imports
import sys
from typing import Any, TextIO, cast

from ..config import StouputilsConfig as Cfg
from .color_formatting import format_colored
from .common import PrintMemory
from .utils import current_time, is_same_print


def info(
	*values: Any,
	color: str = Cfg.GREEN,
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
		use_colored		(bool):					Whether to use the :py:func:`colored` function to format the message
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
			message = f"{Cfg.LINE_UP}{message} (x{PrintMemory.nb_values})"

		# Print the message with the values and reset color
		if use_colored:
			print(message, format_colored(*values).replace(Cfg.RESET, Cfg.RESET+color), Cfg.RESET, file=file, **print_kwargs)
		else:
			print(message, *values, Cfg.RESET, file=file, **print_kwargs)

def debug(*values: Any, flush: bool = True, color: str = Cfg.CYAN, text: str = "DEBUG", **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" in cyan by default. """
	info(*values, flush=flush, color=color, text=text, **print_kwargs)

def alt_debug(*values: Any, flush: bool = True, color: str = Cfg.BLUE, text: str = "DEBUG", **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message" in blue by default. """
	info(*values, flush=flush, color=color, text=text, **print_kwargs)

def suggestion(*values: Any, flush: bool = True, color: str = Cfg.CYAN, text: str = "SUGGESTION", **print_kwargs: Any) -> None:
	""" Print a suggestion message looking like "[SUGGESTION HH:MM:SS] message" in cyan by default. """
	info(*values, flush=flush, color=color, text=text, **print_kwargs)

def progress(*values: Any, flush: bool = True, color: str = Cfg.MAGENTA, text: str = "PROGRESS", **print_kwargs: Any) -> None:
	""" Print a progress message looking like "[PROGRESS HH:MM:SS] message" in magenta by default. """
	info(*values, flush=flush, color=color, text=text, **print_kwargs)

def warning(*values: Any, flush: bool = True, color: str = Cfg.YELLOW, text: str = "WARNING", **print_kwargs: Any) -> None:
	""" Print a warning message looking like "[WARNING HH:MM:SS] message" in yellow by default and in sys.stderr. """
	if "file" not in print_kwargs:
		print_kwargs["file"] = sys.stderr
	info(*values, flush=flush, color=color, text=text, **print_kwargs)

def error(*values: Any, exit: bool = False, flush: bool = True, color: str = Cfg.RED, text: str = "ERROR", **print_kwargs: Any) -> None:
	""" Print an error message (in sys.stderr and in red by default)
	and optionally ask the user to continue or stop the program.

	Args:
		values			(Any):		Values to print (like the print function)
		exit			(bool):		Whether to ask the user to continue or stop the program,
			false to ignore the error automatically and continue
		flush			(bool):		Whether to flush the output
		color			(str):		Color of the message (default: RED)
		text			(str):		Text in the message (replaces "ERROR ")
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	file: TextIO = sys.stderr
	if "file" in print_kwargs:
		if isinstance(print_kwargs["file"], list):
			file = cast(TextIO, print_kwargs["file"][0])
		else:
			file = print_kwargs["file"]
	info(*values, flush=flush, color=color, text=text, **print_kwargs)
	if exit:
		try:
			print("Press enter to ignore error and continue, or 'CTRL+C' to stop the program... ", file=file)
			input()
		except (KeyboardInterrupt, EOFError):
			print(file=file)
			sys.exit(1)




# Convenience colored functions
def infoc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return info(*args, use_colored=use_colored, **kwargs)
def debugc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return debug(*args, use_colored=use_colored, **kwargs)
def alt_debugc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return alt_debug(*args, use_colored=use_colored, **kwargs)
def warningc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return warning(*args, use_colored=use_colored, **kwargs)
def errorc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return error(*args, use_colored=use_colored, **kwargs)
def progressc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return progress(*args, use_colored=use_colored, **kwargs)
def suggestionc(*args: Any, use_colored: bool = True, **kwargs: Any) -> None:
	return suggestion(*args, use_colored=use_colored, **kwargs)

