"""
This module provides utility functions for parallel processing, such as:

- multiprocessing(): Execute a function in parallel using multiprocessing
- multithreading(): Execute a function in parallel using multithreading

I highly encourage you to read the function docstrings to understand when to use each method.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/parallel_module.gif
  :alt: stouputils parallel examples
"""

# Imports
import time
import multiprocessing as mp
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, cpu_count
from typing import Any, TypeVar

from tqdm.auto import tqdm
from tqdm.contrib.concurrent import process_map  # type: ignore

from .decorators import LogLevels, handle_error
from .print import MAGENTA, RESET


# Small test functions for doctests
def doctest_square(x: int) -> int:
	return x * x
def doctest_slow(x: int) -> int:
	time.sleep(0.1)
	return x

# Constants
CPU_COUNT: int = cpu_count()
BAR_FORMAT: str = "{l_bar}{bar}" + MAGENTA + "| {n_fmt}/{total_fmt} [{rate_fmt}{postfix}, {elapsed}<{remaining}]" + RESET
T = TypeVar("T")
R = TypeVar("R")

# Private function to use starmap
def __starmap(args: tuple[Callable[[T], R], list[T]]) -> list[R]:
	func, arguments = args
	return func(*arguments) # type: ignore

# Private function to apply delay before calling the target function
def __delayed_call(args: tuple[Callable[[T], R], float, T]) -> R:
	func, delay, arg = args
	time.sleep(delay)
	return func(arg)

def __handle_parameters(
	func: Callable[[T], R],
	args: list[T],
	use_starmap: bool,
	delay_first_calls: float,
	max_workers: int,
	desc: str,
	color: str
) -> tuple[str, Callable[[T], R], list[T]]:
	r""" Private function to handle the parameters for multiprocessing or multithreading functions

	Args:
		func				(Callable):			Function to execute
		args				(list):				List of arguments to pass to the function
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

	# If use_starmap is True, we use the __starmap function
	if use_starmap:
		args = [(func, arg) for arg in args] # type: ignore
		func = __starmap # type: ignore

	# Prepare delayed function calls if delay_first_calls is set
	if delay_first_calls > 0:
		args = [
			(func, i * delay_first_calls if i < max_workers else 0, arg) # type: ignore
			for i, arg in enumerate(args)
		]
		func = __delayed_call  # type: ignore

	return desc, func, args

@handle_error(error_log=LogLevels.ERROR_TRACEBACK)
def multiprocessing(
	func: Callable[[T], R],
	args: list[T],
	use_starmap: bool = False,
	chunksize: int = 1,
	desc: str = "",
	max_workers: int = CPU_COUNT,
	delay_first_calls: float = 0,
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
) -> list[R]:
	r""" Method to execute a function in parallel using multiprocessing, you should use it:

	- For CPU-bound operations where the GIL (Global Interpreter Lock) is a bottleneck.
	- When the task can be divided into smaller, independent sub-tasks that can be executed concurrently.
	- For computationally intensive tasks like scientific simulations, data analysis, or machine learning workloads.

	Args:
		func				(Callable):			Function to execute
		args				(list):				List of arguments to pass to the function
		use_starmap			(bool):				Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(\*args[i]) instead of func(args[i])
		chunksize			(int):				Number of arguments to process at a time
			(Defaults to 1 for proper progress bar display)
		desc				(str):				Description displayed in the progress bar
			(if not provided no progress bar will be displayed)
		max_workers			(int):				Number of workers to use (Defaults to CPU_COUNT)
		delay_first_calls	(float):			Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance, the first process will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		color				(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format			(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii				(bool):				Whether to use ASCII or Unicode characters for the progress bar

	Returns:
		list[object]:	Results of the function execution

	Examples:
		.. code-block:: python

			> multiprocessing(doctest_square, args=[1, 2, 3])
			[1, 4, 9]

			> multiprocessing(int.__mul__, [(1,2), (3,4), (5,6)], use_starmap=True)
			[2, 12, 30]

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
	# Handle parameters
	verbose: bool = desc != ""
	desc, func, args = __handle_parameters(func, args, use_starmap, delay_first_calls, max_workers, desc, color)
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)

	# Do multiprocessing only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		def process() -> list[Any]:
			if verbose:
				return list(process_map(
					func, args, max_workers=max_workers, chunksize=chunksize, desc=desc, bar_format=bar_format, ascii=ascii
				)) # type: ignore
			else:
				with Pool(max_workers) as pool:
					return list(pool.map(func, args, chunksize=chunksize))	# type: ignore
		try:
			return process()
		except RuntimeError as e:
			if "SemLock created in a fork context is being shared with a process in a spawn context" in str(e):

				# Try with alternate start method
				old_method: str | None = mp.get_start_method(allow_none=True)
				new_method: str = "spawn" if old_method in (None, "fork") else "fork"
				mp.set_start_method(new_method, force=True)
				
				try:
					return process()
				finally:
					mp.set_start_method(old_method, force=True)
			else: # Re-raise if it's not the SemLock error
				raise

	# Single process execution
	else:
		if verbose:
			return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=bar_format, ascii=ascii)]
		else:
			return [func(arg) for arg in args]


@handle_error(error_log=LogLevels.ERROR_TRACEBACK)
def multithreading(
	func: Callable[[T], R],
	args: list[T],
	use_starmap: bool = False,
	desc: str = "",
	max_workers: int = CPU_COUNT,
	delay_first_calls: float = 0,
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
	) -> list[R]:
	r""" Method to execute a function in parallel using multithreading, you should use it:

	- For I/O-bound operations where the GIL is not a bottleneck, such as network requests or disk operations.
	- When the task involves waiting for external resources, such as network responses or user input.
	- For operations that involve a lot of waiting, such as GUI event handling or handling user input.

	Args:
		func				(Callable):			Function to execute
		args				(list):				List of arguments to pass to the function
		use_starmap			(bool):				Whether to use starmap or not (Defaults to False):
			True means the function will be called like func(\*args[i]) instead of func(args[i])
		desc				(str):				Description displayed in the progress bar
			(if not provided no progress bar will be displayed)
		max_workers			(int):				Number of workers to use (Defaults to CPU_COUNT)
		delay_first_calls	(float):			Apply i*delay_first_calls seconds delay to the first "max_workers" calls.
			For instance with value to 1, the first thread will be delayed by 0 seconds, the second by 1 second, etc.
			(Defaults to 0): This can be useful to avoid functions being called in the same second.
		color				(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format			(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii				(bool):				Whether to use ASCII or Unicode characters for the progress bar

	Returns:
		list[object]:	Results of the function execution

	Examples:
		.. code-block:: python

			> multithreading(doctest_square, args=[1, 2, 3])
			[1, 4, 9]

			> multithreading(int.__mul__, [(1,2), (3,4), (5,6)], use_starmap=True)
			[2, 12, 30]

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
	# Handle parameters
	verbose: bool = desc != ""
	desc, func, args = __handle_parameters(func, args, use_starmap, delay_first_calls, max_workers, desc, color)
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)

	# Do multithreading only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		if verbose:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(tqdm(executor.map(func, args), total=len(args), desc=desc, bar_format=bar_format, ascii=ascii))
		else:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(executor.map(func, args))

	# Single process execution
	else:
		if verbose:
			return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=bar_format, ascii=ascii)]
		else:
			return [func(arg) for arg in args]


def colored_for_loop(
	iterable: list[T],
	desc: str = "Processing",
	color: str = MAGENTA,
	bar_format: str = BAR_FORMAT,
	ascii: bool = False,
	**kwargs: Any
) -> Iterator[T]:
	""" Function to iterate over a list with a colored TQDM progress bar like the other functions in this module.

	Args:
		iterable	(list):				List to iterate over
		desc		(str):				Description of the function execution displayed in the progress bar
		color		(str):				Color of the progress bar (Defaults to MAGENTA)
		bar_format	(str):				Format of the progress bar (Defaults to BAR_FORMAT)
		ascii		(bool):				Whether to use ASCII or Unicode characters for the progress bar (Defaults to False)
		verbose		(int):				Level of verbosity, decrease by 1 for each depth (Defaults to 1)
		**kwargs:						Additional arguments to pass to the TQDM progress bar

	Yields:
		T:		Each item of the iterable

	Examples:
		>>> for i in colored_for_loop(range(10), desc="Time sleeping loop"):
		...     time.sleep(0.01)
		>>> # Time sleeping loop: 100%|██████████████████| 10/10 [ 95.72it/s, 00:00<00:00]
	"""
	if bar_format == BAR_FORMAT:
		bar_format = bar_format.replace(MAGENTA, color)
	desc = color + desc

	yield from tqdm(iterable, desc=desc, bar_format=bar_format, ascii=ascii, **kwargs)

