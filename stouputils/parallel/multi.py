
# Imports
import time
from collections.abc import Callable, Iterable
from typing import Any

from ..ctx import SetMPStartMethod
from ..print import BAR_FORMAT, MAGENTA
from .capturer import CaptureOutput
from .common import CPU_COUNT, handle_parameters, nice_wrapper, resolve_process_title


# Small test functions for doctests
def doctest_square(x: int) -> int:
	return x * x
def doctest_slow(x: int) -> int:
	time.sleep(0.1)
	return x

# Functions
def multiprocessing[T, R](
	func: Callable[..., R] | list[Callable[..., R]],
	args: Iterable[T],
	use_starmap: bool = False,
	chunksize: int = 1,
	desc: str = "",
	max_workers: int | float = CPU_COUNT,
	capture_output: bool = False,
	delay_first_calls: float = 0,
	nice: int | None = None,
	process_title: str | None = None,
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
	smooth_tqdm: bool = True,
	**tqdm_kwargs: Any
) -> list[R]:
	r""" Method to execute a function in parallel using multiprocessing

	- For CPU-bound operations where the GIL (Global Interpreter Lock) is a bottleneck.
	- When the task can be divided into smaller, independent sub-tasks that can be executed concurrently.
	- For computationally intensive tasks like scientific simulations, data analysis, or machine learning workloads.

	Args:
		func				(Callable | list[Callable]):	Function to execute, or list of functions (one per argument)
		args				(Iterable):			Iterable of arguments to pass to the function(s)
		use_starmap			(bool):				Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(\*args[i]) instead of func(args[i])
		chunksize			(int):				Number of arguments to process at a time
			(Defaults to 1 for proper progress bar display)
		desc				(str):				Description displayed in the progress bar
			(if not provided no progress bar will be displayed)
		max_workers			(int | float):		Number of workers to use (Defaults to CPU_COUNT), -1 means CPU_COUNT.
			If float between 0 and 1, it's treated as a percentage of CPU_COUNT.
			If negative float between -1 and 0, it's treated as a percentage of len(args).
		capture_output		(bool):				Whether to capture stdout/stderr from the worker processes (Defaults to True)
		delay_first_calls	(float):			Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance, the first process will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		nice				(int | None):		Adjust the priority of worker processes (Defaults to None).
			Use Unix-style values: -20 (highest priority) to 19 (lowest priority).
			Positive values reduce priority, negative values increase it.
			Automatically converted to appropriate priority class on Windows.
			If None, no priority adjustment is made.
		process_title		(str | None):		If provided, sets the process title for worker processes.
			If it starts with '+++', this prefix is replaced by the current process title.
		color				(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format			(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii				(bool):				Whether to use ASCII or Unicode characters for the progress bar
		smooth_tqdm			(bool):				Whether to enable smooth progress bar updates by setting miniters and mininterval (Defaults to True)
		**tqdm_kwargs		(Any):				Additional keyword arguments to pass to tqdm

	Returns:
		list[object]:	Results of the function execution

	Examples:
		.. code-block:: python

			> multiprocessing(doctest_square, args=[1, 2, 3])
			[1, 4, 9]

			> multiprocessing(int.__mul__, [(1,2), (3,4), (5,6)], use_starmap=True)
			[2, 12, 30]

			> # Using a list of functions (one per argument)
			> multiprocessing([doctest_square, doctest_square, doctest_square], [1, 2, 3])
			[1, 4, 9]

			> # Will process in parallel with progress bar
			> multiprocessing(doctest_slow, range(10), desc="Processing")
			[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

			> # Will process in parallel with progress bar and delay the first threads
			> multiprocessing(
			.     doctest_slow,
			.     range(10),
			.     desc="Processing with delay",
			.     max_workers=2,
			.     delay_first_calls=0.6,
			.     process_title="+++ (Worker)"
			. )
			[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	"""
	# Imports
	import multiprocessing as mp
	from concurrent.futures import ProcessPoolExecutor

	from tqdm.auto import tqdm
	from tqdm.contrib.concurrent import process_map  # pyright: ignore[reportUnknownVariableType]

	# Handle parameters
	args = list(args)  # Ensure we have a list (not other iterable)
	if max_workers == -1:
		max_workers = CPU_COUNT
	if isinstance(max_workers, float):
		if max_workers > 0:
			assert max_workers <= 1, "max_workers as positive float must be between 0 and 1 (percentage of CPU_COUNT)"
			max_workers = int(max_workers * CPU_COUNT)
		else:
			assert -1 <= max_workers < 0, "max_workers as negative float must be between -1 and 0 (percentage of len(args))"
			max_workers = int(-max_workers * len(args))
	verbose: bool = desc != ""
	desc, func, args = handle_parameters(func, args, use_starmap, delay_first_calls, max_workers, desc, color)
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)
	if smooth_tqdm:
		tqdm_kwargs.setdefault("mininterval", 0.0)
		try:
			total = len(args) # type: ignore
			import shutil
			width = shutil.get_terminal_size().columns
			tqdm_kwargs.setdefault("miniters", max(1, total // width))
		except (TypeError, OSError):
			tqdm_kwargs.setdefault("miniters", 1)

	# Do multiprocessing only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		# Wrap function with nice if specified
		if nice is not None:
			wrapped_args = [(nice, func, arg) for arg in args]
			wrapped_func = nice_wrapper
		else:
			wrapped_args = args
			wrapped_func = func

		# Wrap function with process_title if specified
		if process_title is not None:
			process_title = resolve_process_title(process_title)
			wrapped_args = [(process_title, i, wrapped_func, arg) for i, arg in enumerate(wrapped_args)]
			wrapped_func = process_title_wrapper

		# Capture output if specified
		capturer: CaptureOutput | None = None
		if capture_output:
			capturer = CaptureOutput()
			capturer.start_listener()
			wrapped_args = [(capturer, wrapped_func, arg) for arg in wrapped_args]
			wrapped_func = capture_subprocess_output

		def process() -> list[Any]:
			if verbose:
				return list(process_map(
					wrapped_func, wrapped_args, max_workers=max_workers, chunksize=chunksize, desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs
				)) # type: ignore
			else:
				with ProcessPoolExecutor(max_workers=max_workers) as executor:
					return list(executor.map(wrapped_func, wrapped_args, chunksize=chunksize))
		try:
			return process()
		except RuntimeError as e:
			if "SemLock created in a fork context is being shared with a process in a spawn context" in str(e):

				# Try with alternate start method
				with SetMPStartMethod("spawn" if mp.get_start_method() != "spawn" else "fork"):
					return process()
			else: # Re-raise if it's not the SemLock error
				raise
		finally:
			if capturer is not None:
				capturer.parent_close_write()
				capturer.join_listener(timeout=5.0)

	# Single process execution
	else:
		if verbose:
			return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs)]
		else:
			return [func(arg) for arg in args]


def multithreading[T, R](
	func: Callable[..., R] | list[Callable[..., R]],
	args: Iterable[T],
	use_starmap: bool = False,
	desc: str = "",
	max_workers: int | float = CPU_COUNT,
	delay_first_calls: float = 0,
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
	smooth_tqdm: bool = True,
	**tqdm_kwargs: Any
	) -> list[R]:
	r""" Method to execute a function in parallel using multithreading, you should use it:

	- For I/O-bound operations where the GIL is not a bottleneck, such as network requests or disk operations.
	- When the task involves waiting for external resources, such as network responses or user input.
	- For operations that involve a lot of waiting, such as GUI event handling or handling user input.

	Args:
		func				(Callable | list[Callable]):	Function to execute, or list of functions (one per argument)
		args				(Iterable):			Iterable of arguments to pass to the function(s)
		use_starmap			(bool):				Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(\*args[i]) instead of func(args[i])
		desc				(str):				Description displayed in the progress bar
			(if not provided no progress bar will be displayed)
		max_workers			(int | float):		Number of workers to use (Defaults to CPU_COUNT), -1 means CPU_COUNT.
			If float between 0 and 1, it's treated as a percentage of CPU_COUNT.
			If negative float between -1 and 0, it's treated as a percentage of len(args).
		delay_first_calls	(float):			Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance with value to 1, the first thread will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		color				(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format			(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii				(bool):				Whether to use ASCII or Unicode characters for the progress bar
		smooth_tqdm			(bool):				Whether to enable smooth progress bar updates by setting miniters and mininterval (Defaults to True)
		**tqdm_kwargs		(Any):				Additional keyword arguments to pass to tqdm

	Returns:
		list[object]:	Results of the function execution

	Examples:
		.. code-block:: python

			> multithreading(doctest_square, args=[1, 2, 3])
			[1, 4, 9]

			> multithreading(int.__mul__, [(1,2), (3,4), (5,6)], use_starmap=True)
			[2, 12, 30]

			> # Using a list of functions (one per argument)
			> multithreading([doctest_square, doctest_square, doctest_square], [1, 2, 3])
			[1, 4, 9]

			> # Will process in parallel with progress bar
			> multithreading(doctest_slow, range(10), desc="Threading")
			[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

			> # Will process in parallel with progress bar and delay the first threads
			> multithreading(
			.     doctest_slow,
			.     range(10),
			.     desc="Threading with delay",
			.     max_workers=2,
			.     delay_first_calls=0.6
			. )
			[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	"""
	# Imports
	from concurrent.futures import ThreadPoolExecutor

	from tqdm.auto import tqdm

	# Handle parameters
	args = list(args)  # Ensure we have a list (not other iterable)
	if max_workers == -1:
		max_workers = CPU_COUNT
	if isinstance(max_workers, float):
		if max_workers > 0:
			assert max_workers <= 1, "max_workers as positive float must be between 0 and 1 (percentage of CPU_COUNT)"
			max_workers = int(max_workers * CPU_COUNT)
		else:
			assert -1 <= max_workers < 0, "max_workers as negative float must be between -1 and 0 (percentage of len(args))"
			max_workers = int(-max_workers * len(args))
	verbose: bool = desc != ""
	desc, func, args = handle_parameters(func, args, use_starmap, delay_first_calls, max_workers, desc, color)
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)
	if smooth_tqdm:
		tqdm_kwargs.setdefault("mininterval", 0.0)
		try:
			total = len(args) # type: ignore
			import shutil
			width = shutil.get_terminal_size().columns
			tqdm_kwargs.setdefault("miniters", max(1, total // width))
		except (TypeError, OSError):
			tqdm_kwargs.setdefault("miniters", 1)

	# Do multithreading only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		if verbose:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(tqdm(executor.map(func, args), total=len(args), desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs))
		else:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(executor.map(func, args))

	# Single process execution
	else:
		if verbose:
			return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs)]
		else:
			return [func(arg) for arg in args]


# "Private" function for capturing multiprocessing subprocess
def capture_subprocess_output[T, R](args: tuple[CaptureOutput, Callable[[T], R], T]) -> R:
	""" Wrapper function to execute the target function in a subprocess with optional output capture.

	Args:
		tuple[CaptureOutput,Callable,T]: Tuple containing:
			CaptureOutput: Capturer object to redirect stdout/stderr
			Callable: Target function to execute
			T: Argument to pass to the target function
	"""
	capturer, func, arg = args
	capturer.redirect()
	return func(arg)


# "Private" function for setting process title in multiprocessing subprocess
def process_title_wrapper[T, R](args: tuple[str, int, Callable[[T], R], T]) -> R:
	""" Wrapper function to set the process title before executing the target function.

	Behavior depends on StouputilsConfig.PROCESS_TITLE_PER_WORKER:
	- If True: Title is set only once per worker, index reflects worker number (0 to max_workers-1)
	- If False: Title is updated for each task, index reflects task number (0 to len(args)-1)

	Args:
		tuple[str,int,Callable,T]: Tuple containing:
			str: Process title to set
			int: Worker index to append to title
			Callable: Target function to execute
			T: Argument to pass to the target function
	"""
	process_title, index, func, arg = args
	import setproctitle

	from ..config import StouputilsConfig

	if StouputilsConfig.PROCESS_TITLE_PER_WORKER:
		current_title = setproctitle.getproctitle()
		# Only set title if it hasn't been set yet (doesn't start with our prefix)
		if not current_title.startswith(process_title):
			setproctitle.setproctitle(f"{process_title} #{index}")
	else:
		# Always update the title for each task
		setproctitle.setproctitle(f"{process_title} #{index}")

	return func(arg)

