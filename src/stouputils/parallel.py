"""
This module provides utility functions for parallel processing, such as:
- multiprocessing(): Execute a function in parallel using multiprocessing
- multithreading(): Execute a function in parallel using multithreading

I highly encourage you to read the function docstrings to understand when to use each method.
"""

# Imports
from .print import *
from .decorators import *
from multiprocessing import Pool, cpu_count
from typing import Callable, TypeVar
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map # type: ignore
from concurrent.futures import ThreadPoolExecutor

# Small test functions for doctests
def doctest_square(x: int) -> int:
	return x * x
def doctest_multiply(x: int, y: int) -> int:
	return x * y
def doctest_slow(x: int) -> int:
	import time
	time.sleep(0.5)
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

@handle_error(error_log=LogLevels.ERROR_TRACEBACK)
def multiprocessing(func: Callable[[T], R], args: list[T], use_starmap: bool = False, chunksize: int = 1, desc: str = "", max_workers: int = CPU_COUNT, verbose_depth: int = 0) -> list[R]:
	""" Method to execute a function in parallel using multiprocessing, you should use it:
	- For CPU-bound operations where the GIL (Global Interpreter Lock) is a bottleneck.
	- When the task can be divided into smaller, independent sub-tasks that can be executed concurrently.
	- For operations that involve heavy computations, such as scientific simulations, data processing, or machine learning tasks.

	Args:
		func			(Callable):			Function to execute
		args			(list):				List of arguments to pass to the function (no starmap will be used)
		use_starmap		(bool):				Whether to use starmap or not (Defaults to False)
		chunksize		(int):				Number of arguments to process at a time (Defaults to 1 for proper progress bar display)
		desc			(str):				Description of the function execution displayed in the progress bar
		max_workers		(int):				Number of workers to use (Defaults to CPU_COUNT)
		verbose_depth	(int):				Level of verbosity, decrease by 1 for each depth
	Returns:
		list[object]:	Results of the function execution
	Examples:
		>>> multiprocessing(doctest_square, args=[1, 2, 3])
		[1, 4, 9]

		>>> multiprocessing(doctest_multiply, [(1,2), (3,4), (5,6)], use_starmap=True)
		[2, 12, 30]

		>>> # Will process in parallel with progress bar
		>>> multiprocessing(doctest_slow, list(range(10)), desc="Processing", verbose_depth=1)
		[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	"""
	if not desc:
		desc = func.__name__
	desc = MAGENTA + desc
	
	# If use_starmap is True, we use the __starmap function
	if use_starmap:
		args = [(func, arg) for arg in args] # type: ignore
		func = __starmap # type: ignore

	# Do multiprocessing only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		if verbose_depth > 0:
			return list(process_map(func, args, max_workers=max_workers, chunksize=chunksize, desc=desc, bar_format=BAR_FORMAT)) # type: ignore
		else:
			with Pool(max_workers) as pool:
				return list(pool.map(func, args, chunksize=chunksize))	# type: ignore

	# Single process execution
	else:
		if verbose_depth > 0:
			return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=BAR_FORMAT)]
		else:
			return [func(arg) for arg in args]


@handle_error(error_log=LogLevels.ERROR_TRACEBACK)
def multithreading(func: Callable[[T], R], args: list[T], use_starmap: bool = False, desc: str = "", max_workers: int = CPU_COUNT, verbose_depth: int = 0) -> list[R]:
	""" Method to execute a function in parallel using multithreading, you should use it:
	- For I/O-bound operations where the GIL is not a bottleneck, such as network requests or disk operations.
	- When the task involves waiting for external resources, such as network responses or user input.
	- For operations that involve a lot of waiting, such as GUI event handling or handling user input.

	Args:
		func			(Callable):			Function to execute
		args			(list):				List of arguments to pass to the function (no starmap will be used)
		use_starmap		(bool):				Whether to use starmap or not (Defaults to False)
		desc			(str):				Description of the function execution displayed in the progress bar
		max_workers		(int):				Number of workers to use (Defaults to CPU_COUNT)
		verbose_depth	(int):				Level of verbosity, decrease by 1 for each depth
	Returns:
		list[object]:	Results of the function execution
	Examples:
		>>> multithreading(doctest_square, args=[1, 2, 3])
		[1, 4, 9]

		>>> multithreading(doctest_multiply, [(1,2), (3,4), (5,6)], use_starmap=True)
		[2, 12, 30]

		>>> # Will process in parallel with progress bar
		>>> multithreading(doctest_slow, list(range(10)), desc="Threading", verbose_depth=1)
		[0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
	"""
	if not desc:
		desc = func.__name__
	desc = MAGENTA + desc
	
	# If use_starmap is True, we use the __starmap function
	if use_starmap:
		args = [(func, arg) for arg in args] # type: ignore
		func = __starmap # type: ignore

	# Do multithreading only if there is more than 1 argument and more than 1 CPU
	if max_workers > 1 and len(args) > 1:
		if verbose_depth > 0:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(tqdm(executor.map(func, args), total=len(args), desc=desc, bar_format=BAR_FORMAT))
		else:
			with ThreadPoolExecutor(max_workers) as executor:
				return list(executor.map(func, args))

	# Single process execution
	else:
		if verbose_depth > 0:
			return [func(arg) for arg in tqdm(args, total=len(args), desc=desc, bar_format=BAR_FORMAT)]
		else:
			return [func(arg) for arg in args]

