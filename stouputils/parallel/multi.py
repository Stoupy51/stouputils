
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import sys
import time
from collections.abc import Callable, Iterable
from typing import Any

from ..config import StouputilsConfig as Cfg
from ..ctx.set_mp_start_method import SetMPStartMethod
from ..typing import JsonList
from .capturer import CaptureOutput
from .common import nice_wrapper, normalize_parallel_params, resolve_process_title, run_sequential


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
	max_workers: int | float = Cfg.CPU_COUNT,
	capture_output: bool = True,
	delay_first_calls: float = 0,
	nice: int | None = None,
	process_title: str | None = None,
	color: str = Cfg.MAGENTA,
	bar_format: str = Cfg.BAR_FORMAT,
	ascii: bool = False,
	smooth_tqdm: bool = True,
	**tqdm_kwargs: Any
) -> list[R]:
	r""" Method to execute a function in parallel using multiprocessing

	- For CPU-bound operations where the GIL (Global Interpreter Lock) is a bottleneck.
	- When the task can be divided into smaller, independent sub-tasks that can be executed concurrently.
	- For computationally intensive tasks like scientific simulations, data analysis, or machine learning workloads.

	Args:
		func:              Function to execute, or list of functions (one per argument)
		args:              Iterable of arguments to pass to the function(s)
		use_starmap:       Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(*args[i]) instead of func(args[i])
		chunksize:         Number of arguments to process at a time
			(Defaults to 1 for proper progress bar display)
		desc:              Description displayed in the progress bar
			(if not provided no progress bar will be displayed)
		max_workers:       Number of workers to use (Defaults to CPU_COUNT), -1 means CPU_COUNT.
			If float between 0 and 1, it's treated as a percentage of CPU_COUNT.
			If negative float between -1 and 0, it's treated as a percentage of len(args).
		capture_output:    Whether to capture stdout/stderr from the worker processes (Defaults to True)
		delay_first_calls: Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance, the first process will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		nice:              Adjust the priority of worker processes (Defaults to None).
			Use Unix-style values: -20 (highest priority) to 19 (lowest priority).
			Positive values reduce priority, negative values increase it.
			Automatically converted to appropriate priority class on Windows.
			If None, no priority adjustment is made.
		process_title:     If provided, sets the process title for worker processes.
			If it starts with '+++', this prefix is replaced by the current process title.
		color:             Color of the progress bar (Defaults to MAGENTA)
		bar_format:        Format of the progress bar (Defaults to BAR_FORMAT)
		ascii:             Whether to use ASCII or Unicode characters for the progress bar
		smooth_tqdm:       Whether to enable smooth progress bar updates by setting miniters and mininterval (Defaults to True)
		**tqdm_kwargs:     Additional keyword arguments to pass to tqdm
	Returns:
		Results of the function execution
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
	import multiprocessing as mp

	# Handle parameters
	args, max_workers, verbose, desc, task, bar_format = normalize_parallel_params(
		func, args, use_starmap, delay_first_calls, max_workers, desc, color, bar_format, smooth_tqdm, tqdm_kwargs
	)

	# Do multiprocessing only if there is more than 1 argument and more than 1 CPU
	if max_workers <= 1 or len(args) <= 1:
		return run_sequential(task, args, verbose, desc, bar_format, ascii, tqdm_kwargs)

	capturer: CaptureOutput | None = CaptureOutput() if capture_output else None
	if capturer is not None:
		capturer.start_listener()
	worker_func, worker_args = wrap_for_workers(task, args, nice, resolve_process_title(process_title), capturer)
	try:
		return run_pool(worker_func, worker_args, max_workers, chunksize, verbose, desc, bar_format, ascii, tqdm_kwargs)
	except RuntimeError as e:
		if "SemLock created in a fork context is being shared with a process in a spawn context" not in str(e):
			raise
		with SetMPStartMethod("spawn" if mp.get_start_method() != "spawn" else "fork"):
			return run_pool(worker_func, worker_args, max_workers, chunksize, verbose, desc, bar_format, ascii, tqdm_kwargs)
	finally:
		if capturer is not None:
			capturer.parent_close_write()
			capturer.join_listener(timeout=5.0)


def wrap_for_workers(
	func: Callable[..., Any], args: list[Any], nice: int | None, process_title: str | None, capturer: CaptureOutput | None
) -> tuple[Callable[..., Any], list[Any]]:
	""" The function workers call and its arguments, wrapped in turn for the niceness, process title and output capture asked for.

	Args:
		process_title: Title already resolved by :func:`resolve_process_title`, None to leave the title alone.
	"""
	if nice is not None:
		args, func = [(nice, func, arg) for arg in args], nice_wrapper
	if process_title is not None:
		args, func = [(process_title, i, func, arg) for i, arg in enumerate(args)], process_title_wrapper
	if capturer is not None:
		args, func = [(capturer, func, arg) for arg in args], capture_subprocess_output
	return func, args


def run_pool(
	func: Callable[..., Any],
	args: list[Any],
	max_workers: int,
	chunksize: int,
	verbose: bool,
	desc: str,
	bar_format: str,
	ascii: bool,
	tqdm_kwargs: dict[str, Any],
) -> JsonList:
	""" Map func over args in a process pool, behind a tqdm progress bar when verbose. """
	if verbose:
		from tqdm.contrib.concurrent import process_map  # pyright: ignore[reportUnknownVariableType]
		return list(process_map(  # pyright: ignore[reportCallIssue, reportUnknownArgumentType]
			func, args, max_workers=max_workers, chunksize=chunksize, desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs,
		))
	from concurrent.futures import ProcessPoolExecutor
	with ProcessPoolExecutor(max_workers=max_workers) as executor:
		return list(executor.map(func, args, chunksize=chunksize))


def multithreading[T, R](
	func: Callable[..., R] | list[Callable[..., R]],
	args: Iterable[T],
	use_starmap: bool = False,
	desc: str = "",
	max_workers: int | float = Cfg.CPU_COUNT,
	delay_first_calls: float = 0,
	color: str = Cfg.MAGENTA,
	bar_format: str = Cfg.BAR_FORMAT,
	ascii: bool = False,
	smooth_tqdm: bool = True,
	**tqdm_kwargs: Any
	) -> list[R]:
	r""" Method to execute a function in parallel using multithreading, you should use it:

	- For I/O-bound operations where the GIL is not a bottleneck, such as network requests or disk operations.
	- When the task involves waiting for external resources, such as network responses or user input.
	- For operations that involve a lot of waiting, such as GUI event handling or handling user input.

	Args:
		func:              Function to execute, or list of functions (one per argument)
		args:              Iterable of arguments to pass to the function(s)
		use_starmap:       Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(*args[i]) instead of func(args[i])
		desc:              Description displayed in the progress bar
			(if not provided no progress bar will be displayed)
		max_workers:       Number of workers to use (Defaults to CPU_COUNT), -1 means CPU_COUNT.
			If float between 0 and 1, it's treated as a percentage of CPU_COUNT.
			If negative float between -1 and 0, it's treated as a percentage of len(args).
		delay_first_calls: Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance with value to 1, the first thread will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		color:             Color of the progress bar (Defaults to MAGENTA)
		bar_format:        Format of the progress bar (Defaults to BAR_FORMAT)
		ascii:             Whether to use ASCII or Unicode characters for the progress bar
		smooth_tqdm:       Whether to enable smooth progress bar updates by setting miniters and mininterval (Defaults to True)
		**tqdm_kwargs:     Additional keyword arguments to pass to tqdm
	Returns:
		Results of the function execution
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
	args, max_workers, verbose, desc, func, bar_format = normalize_parallel_params(
		func, args, use_starmap, delay_first_calls, max_workers, desc, color, bar_format, smooth_tqdm, tqdm_kwargs
	)

	# Do multithreading only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		if verbose:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(tqdm(
					executor.map(func, args), total=len(args), desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs,  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]
				))
		else:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(executor.map(func, args))  # pyright: ignore[reportArgumentType, reportUnknownArgumentType]

	# Single process execution
	else:
		return run_sequential(func, args, verbose, desc, bar_format, ascii, tqdm_kwargs)  # pyright: ignore[reportArgumentType]


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
	try:
		return func(arg)
	finally:
		sys.stdout.flush()


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

	if Cfg.PROCESS_TITLE_PER_WORKER:
		current_title = setproctitle.getproctitle()
		# Only set title if it hasn't been set yet (doesn't start with our prefix)
		if not current_title.startswith(process_title):
			setproctitle.setproctitle(f"{process_title} #{index}")
	else:
		# Always update the title for each task
		setproctitle.setproctitle(f"{process_title} #{index}")

	return func(arg)

