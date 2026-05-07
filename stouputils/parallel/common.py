
# Imports
import os
import time
from collections.abc import Callable, Iterable
from typing import Any, cast

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
def resolve_process_title(process_title: str | None) -> str | None:
	""" Resolve the process title, replacing a leading '+++' with the current process title.

	If ``process_title`` starts with '+++', the '+++' prefix is replaced by the
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
		return current_title + process_title[3:]
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


# Private helper shared by multiprocessing and multithreading to normalize parameters
def normalize_parallel_params(
	func: Callable[..., Any] | list[Callable[..., Any]],
	args: Iterable[Any],
	use_starmap: bool,
	delay_first_calls: float,
	max_workers: int | float,
	desc: str,
	color: str,
	bar_format: str,
	smooth_tqdm: bool,
	tqdm_kwargs: dict[str, Any],
) -> tuple[list[Any], int, bool, str, Any, str]:
	""" Normalize execution parameters shared between multiprocessing and multithreading.

	Handles max_workers normalization, verbose flag, handle_parameters call,
	bar_format color substitution, and smooth_tqdm miniters/mininterval setup.
	Mutates tqdm_kwargs in place for smooth_tqdm settings.

	Returns:
		tuple: (args_list, max_workers_int, verbose, desc, func, bar_format)
	"""
	# Retrieve args
	args_list: list[Any] = list(args)

	# Normalize max_workers
	if max_workers == -1:
		max_workers = Cfg.CPU_COUNT
	if isinstance(max_workers, float):
		if max_workers > 0:
			assert max_workers <= 1, "max_workers as positive float must be between 0 and 1 (percentage of CPU_COUNT)"
			max_workers = int(max_workers * Cfg.CPU_COUNT)
		else:
			assert -1 <= max_workers < 0, "max_workers as negative float must be between -1 and 0 (percentage of len(args))"
			max_workers = int(-max_workers * len(args_list))
	max_workers_int: int = int(max_workers)

	# Determine verbosity and handle parameters
	verbose: bool = desc != ""
	desc, func, args_list = handle_parameters(func, args_list, use_starmap, delay_first_calls, max_workers_int, desc, color)

	# Substitute color in bar_format if it matches the default
	if bar_format == Cfg.BAR_FORMAT:
		bar_format = bar_format.replace(Cfg.MAGENTA, color)

	# Setup tqdm kwargs for smooth progress bar if enabled
	if smooth_tqdm:
		tqdm_kwargs.setdefault("mininterval", 0.0)
		try:
			import shutil
			total: int = len(args_list) # type: ignore
			width: int = shutil.get_terminal_size().columns
			tqdm_kwargs.setdefault("miniters", max(1, total // width))
		except (TypeError, OSError):
			tqdm_kwargs.setdefault("miniters", 1)

	# Return normalized parameters
	return args_list, max_workers_int, verbose, desc, func, bar_format


# Private helper for sequential (single-worker) execution shared by multiprocessing and multithreading
def run_sequential(
	func: Callable[..., Any],
	args: list[Any],
	verbose: bool,
	desc: str,
	bar_format: str,
	ascii: bool,
	tqdm_kwargs: dict[str, Any],
) -> list[Any]:
	""" Execute func over args sequentially, with optional tqdm progress bar. """
	if verbose:
		from tqdm.auto import tqdm
		return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs)]
	return [func(arg) for arg in args]

