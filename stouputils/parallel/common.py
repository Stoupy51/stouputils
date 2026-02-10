
# Imports
import os
import time
from collections.abc import Callable
from typing import cast

# Constants (aliased from configuration)
from ..config import StouputilsConfig as Cfg

CPU_COUNT: int = Cfg.CPU_COUNT


# "Private" function to wrap function execution with nice priority (must be at module level for pickling)
def nice_wrapper[T, R](args: tuple[int, Callable[[T], R], T]) -> R:
	""" Wrapper that applies nice priority then executes the function.

	Args:
		args (tuple): Tuple containing (nice_value, func, arg)

	Returns:
		R: Result of the function execution
	"""
	nice_value, func, arg = args
	set_process_priority(nice_value)
	return func(arg)

# "Private" function to set process priority (must be at module level for pickling on Windows)
def set_process_priority(nice_value: int) -> None:
	""" Set the priority of the current process.

	Args:
		nice_value (int): Unix-style priority value (-20 to 19)
	"""
	try:
		import sys
		if sys.platform == "win32":
			# Map Unix nice values to Windows priority classes
			# -20 to -10: HIGH, -9 to -1: ABOVE_NORMAL, 0: NORMAL, 1-9: BELOW_NORMAL, 10-19: IDLE
			import ctypes
			# Windows priority class constants
			if nice_value <= -10:
				priority = 0x00000080  # HIGH_PRIORITY_CLASS
			elif nice_value < 0:
				priority = 0x00008000  # ABOVE_NORMAL_PRIORITY_CLASS
			elif nice_value == 0:
				priority = 0x00000020  # NORMAL_PRIORITY_CLASS
			elif nice_value < 10:
				priority = 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
			else:
				priority = 0x00000040  # IDLE_PRIORITY_CLASS
			kernel32 = ctypes.windll.kernel32
			handle = kernel32.GetCurrentProcess()
			kernel32.SetPriorityClass(handle, priority)
		else:
			# Unix-like systems
			os.nice(nice_value)
	except Exception:
		pass  # Silently ignore if we can't set priority

# "Private" function to use starmap using args[0](*args[1])
def starmap[T, R](args: tuple[Callable[[T], R], list[T]]) -> R:
	r""" Private function to use starmap using args[0](\*args[1])

	Args:
		args (tuple): Tuple containing the function and the arguments list to pass to the function
	Returns:
		object: Result of the function execution
	"""
	func, arguments = args
	return func(*arguments)

# "Private" function to apply delay before calling the target function
def delayed_call[T, R](args: tuple[Callable[[T], R], float, T]) -> R:
	""" Private function to apply delay before calling the target function

	Args:
		args (tuple): Tuple containing the function, delay in seconds, and the argument to pass to the function
	Returns:
		object: Result of the function execution
	"""
	func, delay, arg = args
	time.sleep(delay)
	return func(arg)

# Function to resolve process title prefix
def resolve_process_title[T: str | None](process_title: T) -> T:
	""" Resolve the process title, replacing a leading '+++' with the current process title.

	If `process_title` starts with '+++', the '+++' prefix is replaced by the
	current process title (retrieved via ``setproctitle.getproctitle()``).
	Otherwise the value is returned unchanged.

	Args:
		process_title (str | None): The desired process title, optionally prefixed with '+++'.

	Returns:
		str | None: The resolved process title, or None if the input was None.

	Examples:
		>>> resolve_process_title(None) is None
		True
		>>> resolve_process_title("my_worker")
		'my_worker'
		>>> import setproctitle
		>>> setproctitle.setproctitle("main_process")
		>>> resolve_process_title("+++_worker")
		'main_process_worker'
	"""
	if process_title is None:
		return process_title
	if process_title.startswith("+++"):
		import setproctitle
		current_title: str = setproctitle.getproctitle()
		return cast(T, current_title + process_title[3:])
	return process_title


# "Private" function to handle parameters for multiprocessing or multithreading functions
def handle_parameters[T, R](
	func: Callable[[T], R] | list[Callable[[T], R]],
	args: list[T],
	use_starmap: bool,
	delay_first_calls: float,
	max_workers: int,
	desc: str,
	color: str
) -> tuple[str, Callable[[T], R], list[T]]:
	r""" Private function to handle the parameters for multiprocessing or multithreading functions

	Args:
		func				(Callable | list[Callable]):	Function to execute, or list of functions (one per argument)
		args				(list):				List of arguments to pass to the function(s)
		use_starmap			(bool):				Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(\*args[i]) instead of func(args[i])
		delay_first_calls	(int):				Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance, the first process will be delayed by 0 seconds, the second by 1 second, etc. (Defaults to 0):
			This can be useful to avoid functions being called in the same second.
		max_workers			(int):				Number of workers to use
		desc				(str):				Description of the function execution displayed in the progress bar
		color				(str):				Color of the progress bar

	Returns:
		tuple[str, Callable[[T], R], list[T]]:	Tuple containing the description, function, and arguments
	"""
	desc = color + desc

	# Handle list of functions: validate and convert to starmap format
	if isinstance(func, list):
		func = cast(list[Callable[[T], R]], func)
		assert len(func) == len(args), f"Length mismatch: {len(func)} functions but {len(args)} arguments"
		args = [(f, arg if use_starmap else (arg,)) for f, arg in zip(func, args, strict=False)] # type: ignore
		func = starmap # type: ignore

	# If use_starmap is True, we use the _starmap function
	elif use_starmap:
		args = [(func, arg) for arg in args] # type: ignore
		func = starmap # type: ignore

	# Prepare delayed function calls if delay_first_calls is set
	if delay_first_calls > 0:
		args = [
			(func, i * delay_first_calls if i < max_workers else 0, arg) # type: ignore
			for i, arg in enumerate(args)
		]
		func = delayed_call  # type: ignore

	return desc, func, args # type: ignore

