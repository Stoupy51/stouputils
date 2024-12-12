"""
This module provides utility functions for printing messages with different levels of importance, such as:
- info()
- debug()
- suggestion()
- progress()
- warning()
- error()

It also includes a function to print the type of each value and the value itself:
- whatisit()
"""

# Imports
import sys
import time
from typing import Callable, Any

# Colors constants
RESET: str   = "\033[0m"
RED: str     = "\033[91m"
GREEN: str   = "\033[92m"
YELLOW: str  = "\033[93m"
BLUE: str    = "\033[94m"
MAGENTA: str = "\033[95m"
CYAN: str    = "\033[96m"
LINE_UP: str = "\033[1A"

# Print functions
previous_args_kwards: tuple[tuple[Any, ...], dict[str, Any]] = ((), {})
nb_values: int = 0

def is_same_print(*args: tuple[Any, ...], **kwargs: dict[str, Any]) -> bool:
	""" Checks if the current print call is the same as the previous one.

	Args:
		args (tuple): The arguments passed to the print function.
		kwargs (dict): The keyword arguments passed to the print function.
	Returns:
		bool: True if the current print call is the same as the previous one, False otherwise.
	"""
	global previous_args_kwards, nb_values
	if previous_args_kwards == (args, kwargs):
		nb_values += 1
		return True
	else:
		previous_args_kwards = (args, kwargs)
		nb_values = 0
		return False

def current_time() -> str:
	""" Get the current time in the format HH:MM:SS	"""
	return time.strftime("%H:%M:%S")

def info(*values: Any, prefix: str = "", **print_kwargs: Any) -> None:
	""" Print an information message looking like "[INFO HH:MM:SS] message"

	Args:
		values			(Any):	Values to print (like the print function)
		prefix			(str):		Prefix to add to the values
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	if not is_same_print(*values, **print_kwargs):
		print(f"{prefix}{GREEN}[INFO  {current_time()}]", *values, RESET, **print_kwargs)
	else:
		print(f"{LINE_UP}{prefix}{GREEN}[INFO  {current_time()}] (x{nb_values})", *values, RESET, **print_kwargs)

def debug(*values: Any, prefix: str = "", **print_kwargs: Any) -> None:
	""" Print a debug message looking like "[DEBUG HH:MM:SS] message"

	Args:
		values			(Any):		Values to print (like the print function)
		prefix			(str):		Prefix to add to the values
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	if not is_same_print(*values, **print_kwargs):
		print(f"{prefix}{BLUE}[DEBUG {current_time()}]", *values, RESET, **print_kwargs)
	else:
		print(f"{LINE_UP}{prefix}{BLUE}[DEBUG {current_time()}] (x{nb_values})", *values, RESET, **print_kwargs)

def suggestion(*values: Any, prefix: str = "", **print_kwargs: Any) -> None:
	""" Print a suggestion message looking like "[SUGGESTION HH:MM:SS] message"

	Args:
		values			(Any):		Values to print (like the print function)
		prefix			(str):		Prefix to add to the values
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	if not is_same_print(*values, **print_kwargs):
		print(f"{prefix}{CYAN}[SUGGESTION {current_time()}]", *values, RESET, **print_kwargs)
	else:
		print(f"{LINE_UP}{prefix}{CYAN}[SUGGESTION {current_time()}] (x{nb_values})", *values, RESET, **print_kwargs)

def progress(*values: Any, prefix: str = "", **print_kwargs: Any) -> None:
	""" Print a progress message looking like "[PROGRESS HH:MM:SS] message"

	Args:
		values			(Any):		Values to print (like the print function)
		prefix			(str):		Prefix to add to the values
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	if not is_same_print(*values, **print_kwargs):
		print(f"{prefix}{MAGENTA}[PROGRESS {current_time()}]", *values, RESET, **print_kwargs)
	else:
		print(f"{LINE_UP}{prefix}{MAGENTA}[PROGRESS {current_time()}] (x{nb_values})", *values, RESET, **print_kwargs)

def warning(*values: Any, prefix: str = "", **print_kwargs: Any) -> None:
	""" Print a warning message looking like "[WARNING HH:MM:SS] message"

	Args:
		values			(Any):		Values to print (like the print function)
		prefix			(str):		Prefix to add to the values
		print_kwargs	(dict):		Keyword arguments to pass to the print function
	"""
	if not is_same_print(*values, **print_kwargs):
		print(f"{prefix}{YELLOW}[WARNING {current_time()}]", *values, RESET, **print_kwargs)
	else:
		print(f"{LINE_UP}{prefix}{YELLOW}[WARNING {current_time()}] (x{nb_values})", *values, RESET, **print_kwargs)

def error(*values: Any, exit: bool = True, prefix: str = "", **print_kwargs: Any) -> None:
	""" Print an error message and optionally ask the user to continue or stop the program

	Args:
		values			(Any):		Values to print (like the print function)
		exit			(bool):			Whether to ask the user to continue or stop the program, false to ignore the error automatically and continue
		print_kwargs	(dict):			Keyword arguments to pass to the print function
	"""
	if not is_same_print(*values, **print_kwargs):
		print(f"{prefix}{RED}[ERROR {current_time()}]", *values, RESET, **print_kwargs)
	else:
		print(f"{LINE_UP}{prefix}{RED}[ERROR {current_time()}] (x{nb_values})", *values, RESET, **print_kwargs)
	if exit:
		try:
			input("Press enter to ignore error and continue or 'CTRL+C' to stop the program... ")
		except KeyboardInterrupt:
			sys.exit(1)

def whatisit(*values: Any, print_function: Callable[..., None] = debug, prefix: str = "") -> None:
	""" Print the type of each value and the value itself

	Args:
		values			(Any):		Values to print
		print_function	(Callable):	Function to use to print the values
		prefix			(str):		Prefix to add to the values
	"""
	if len(values) > 1:
		print_function("(What is it?)", prefix=prefix)
		for value in values:
			print_function(f"{type(value)}:\t{value}", prefix=prefix)
	elif len(values) == 1:
		print_function(f"(What is it?) {type(values[0])}:\t{values[0]}", prefix=prefix)






if __name__ == "__main__":
	info("Hello", "World")
	time.sleep(1)
	info("Hello", "World")
	time.sleep(1)
	info("Hello", "World")
	time.sleep(1)
	info("Hello", "World")
	time.sleep(1)
	info("Hello", "World")
	time.sleep(1)
	info("Hello", "World")

