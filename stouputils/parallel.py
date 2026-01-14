"""
This module provides utility functions for parallel processing, such as:

- multiprocessing(): Execute a function in parallel using multiprocessing
- multithreading(): Execute a function in parallel using multithreading
- run_in_subprocess(): Execute a function in a subprocess with args and kwargs

I highly encourage you to read the function docstrings to understand when to use each method.

Priority (nice) mapping for multiprocessing():

- Unix-style values from -20 (highest priority) to 19 (lowest priority)
- Windows automatic mapping:
  * -20 to -10: HIGH_PRIORITY_CLASS
  * -9 to -1: ABOVE_NORMAL_PRIORITY_CLASS
  * 0: NORMAL_PRIORITY_CLASS
  * 1 to 9: BELOW_NORMAL_PRIORITY_CLASS
  * 10 to 19: IDLE_PRIORITY_CLASS

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/parallel_module.gif
  :alt: stouputils parallel examples
"""

# Imports
import os
import time
from collections.abc import Callable, Iterable
from typing import Any, TypeVar, cast

from .ctx import SetMPStartMethod
from .print import BAR_FORMAT, MAGENTA


# Small test functions for doctests
def doctest_square(x: int) -> int:
	return x * x
def doctest_slow(x: int) -> int:
	time.sleep(0.1)
	return x

# Constants
CPU_COUNT: int = cast(int, os.cpu_count())
T = TypeVar("T")
R = TypeVar("R")

# Functions
def multiprocessing[T, R](
	func: Callable[..., R] | list[Callable[..., R]],
	args: Iterable[T],
	use_starmap: bool = False,
	chunksize: int = 1,
	desc: str = "",
	max_workers: int | float = CPU_COUNT,
	delay_first_calls: float = 0,
	nice: int | None = None,
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
		delay_first_calls	(float):			Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance, the first process will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		nice				(int | None):		Adjust the priority of worker processes (Defaults to None).
			Use Unix-style values: -20 (highest priority) to 19 (lowest priority).
			Positive values reduce priority, negative values increase it.
			Automatically converted to appropriate priority class on Windows.
			If None, no priority adjustment is made.
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
			.     delay_first_calls=0.6
			. )
			[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	"""
	# Imports
	import multiprocessing as mp
	from multiprocessing import Pool

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
	desc, func, args = _handle_parameters(func, args, use_starmap, delay_first_calls, max_workers, desc, color)
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
		def process() -> list[Any]:
			# Wrap function with nice if specified
			if nice is not None:
				wrapped_args = [(nice, func, arg) for arg in args]
				wrapped_func = _nice_wrapper
			else:
				wrapped_args = args
				wrapped_func = func

			if verbose:
				return list(process_map(
					wrapped_func, wrapped_args, max_workers=max_workers, chunksize=chunksize, desc=desc, bar_format=bar_format, ascii=ascii, **tqdm_kwargs
				)) # type: ignore
			else:
				with Pool(max_workers) as pool:
					return list(pool.map(wrapped_func, wrapped_args, chunksize=chunksize))	# type: ignore
		try:
			return process()
		except RuntimeError as e:
			if "SemLock created in a fork context is being shared with a process in a spawn context" in str(e):

				# Try with alternate start method
				with SetMPStartMethod("spawn" if mp.get_start_method() != "spawn" else "fork"):
					return process()
			else: # Re-raise if it's not the SemLock error
				raise

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
	desc, func, args = _handle_parameters(func, args, use_starmap, delay_first_calls, max_workers, desc, color)
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


def run_in_subprocess[R](
	func: Callable[..., R],
	*args: Any,
	timeout: float | None = None,
	no_join: bool = False,
	**kwargs: Any
) -> R:
	""" Execute a function in a subprocess with positional and keyword arguments.

	This is useful when you need to run a function in isolation to avoid memory leaks,
	resource conflicts, or to ensure a clean execution environment. The subprocess will
	be created, run the function with the provided arguments, and return the result.

	Args:
		func         (Callable):     The function to execute in a subprocess.
			(SHOULD BE A TOP-LEVEL FUNCTION TO BE PICKLABLE)
		*args        (Any):          Positional arguments to pass to the function.
		timeout      (float | None): Maximum time in seconds to wait for the subprocess.
			If None, wait indefinitely. If the subprocess exceeds this time, it will be terminated.
		no_join      (bool):         If True, do not wait for the subprocess to finish (fire-and-forget).
		**kwargs     (Any):          Keyword arguments to pass to the function.

	Returns:
		R: The return value of the function.

	Raises:
		RuntimeError: If the subprocess exits with a non-zero exit code or times out.
		TimeoutError: If the subprocess exceeds the specified timeout.

	Examples:
		.. code-block:: python

			> # Simple function execution
			> run_in_subprocess(doctest_square, 5)
			25

			> # Function with multiple arguments
			> def add(a: int, b: int) -> int:
			.     return a + b
			> run_in_subprocess(add, 10, 20)
			30

			> # Function with keyword arguments
			> def greet(name: str, greeting: str = "Hello") -> str:
			.     return f"{greeting}, {name}!"
			> run_in_subprocess(greet, "World", greeting="Hi")
			'Hi, World!'

			> # With timeout to prevent hanging
			> run_in_subprocess(some_gpu_func, data, timeout=300.0)
	"""
	import multiprocessing as mp
	from multiprocessing import Queue

	# Create a queue to get the result from the subprocess (only if we need to wait)
	result_queue: Queue[R | Exception] | None = None if no_join else Queue()

	# Create and start the subprocess using the module-level wrapper
	process: mp.Process = mp.Process(
		target=_subprocess_wrapper,
		args=(result_queue, func, args, kwargs)
	)
	process.start()

	# Detach process if no_join (fire-and-forget)
	if result_queue is None:
		return None  # type: ignore
	process.join(timeout=timeout)

	# Check if process is still alive (timed out)
	if process.is_alive():
		process.terminate()
		time.sleep(0.5)  # Give it a moment to terminate gracefully
		if process.is_alive():
			process.kill()
		process.join()
		raise TimeoutError(f"Subprocess exceeded timeout of {timeout} seconds and was terminated")

	# Check exit code
	if process.exitcode != 0:
		# Try to get any exception from the queue (non-blocking)
		error_msg = f"Subprocess failed with exit code {process.exitcode}"
		try:
			if not result_queue.empty():
				result_or_exception = result_queue.get_nowait()
				if isinstance(result_or_exception, Exception):
					raise result_or_exception
		except Exception:
			pass
		raise RuntimeError(error_msg)

	# Retrieve the result
	try:
		result_or_exception = result_queue.get_nowait()
		if isinstance(result_or_exception, Exception):
			raise result_or_exception
		return result_or_exception
	except Exception as e:
		raise RuntimeError("Subprocess did not return any result") from e


# "Private" function to wrap function execution with nice priority (must be at module level for pickling)
def _nice_wrapper[T, R](args: tuple[int, Callable[[T], R], T]) -> R:
	""" Wrapper that applies nice priority then executes the function.

	Args:
		args (tuple): Tuple containing (nice_value, func, arg)

	Returns:
		R: Result of the function execution
	"""
	nice_value, func, arg = args
	_set_process_priority(nice_value)
	return func(arg)

# "Private" function to set process priority (must be at module level for pickling on Windows)
def _set_process_priority(nice_value: int) -> None:
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

# "Private" function for subprocess wrapper (must be at module level for pickling on Windows)
def _subprocess_wrapper[R](
	result_queue: Any,
	func: Callable[..., R],
	args: tuple[Any, ...],
	kwargs: dict[str, Any]
) -> None:
	""" Wrapper function to execute the target function and store the result in the queue.

	Must be at module level to be pickable on Windows (spawn context).

	Args:
		result_queue (multiprocessing.Queue | None):  Queue to store the result or exception (None if detached).
		func         (Callable):                            The target function to execute.
		args         (tuple):                               Positional arguments for the function.
		kwargs       (dict):                                Keyword arguments for the function.
	"""
	try:
		result: R = func(*args, **kwargs)
		if result_queue is not None:
			result_queue.put(result)
	except Exception as e:
		if result_queue is not None:
			result_queue.put(e)

# "Private" function to use starmap
def _starmap[T, R](args: tuple[Callable[[T], R], list[T]]) -> R:
	r""" Private function to use starmap using args[0](\*args[1])

	Args:
		args (tuple): Tuple containing the function and the arguments list to pass to the function
	Returns:
		object: Result of the function execution
	"""
	func, arguments = args
	return func(*arguments)

# "Private" function to apply delay before calling the target function
def _delayed_call[T, R](args: tuple[Callable[[T], R], float, T]) -> R:
	""" Private function to apply delay before calling the target function

	Args:
		args (tuple): Tuple containing the function, delay in seconds, and the argument to pass to the function
	Returns:
		object: Result of the function execution
	"""
	func, delay, arg = args
	time.sleep(delay)
	return func(arg)

# "Private" function to handle parameters for multiprocessing or multithreading functions
def _handle_parameters[T, R](
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
		max_workers			(int):				Number of workers to use (Defaults to CPU_COUNT)
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
		func = _starmap # type: ignore

	# If use_starmap is True, we use the _starmap function
	elif use_starmap:
		args = [(func, arg) for arg in args] # type: ignore
		func = _starmap # type: ignore

	# Prepare delayed function calls if delay_first_calls is set
	if delay_first_calls > 0:
		args = [
			(func, i * delay_first_calls if i < max_workers else 0, arg) # type: ignore
			for i, arg in enumerate(args)
		]
		func = _delayed_call  # type: ignore

	return desc, func, args # type: ignore

