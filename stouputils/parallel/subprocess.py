
# Imports
import time
from collections.abc import Callable
from typing import Any, TypeVar

from .capturer import CaptureOutput, PipeWriter

# Constants
R = TypeVar("R")


def run_in_subprocess[R](
	func: Callable[..., R],
	*args: Any,
	timeout: float | None = None,
	no_join: bool = False,
	capture_output: bool = False,
	**kwargs: Any
) -> R:
	""" Execute a function in a subprocess with positional and keyword arguments.

	This is useful when you need to run a function in isolation to avoid memory leaks,
	resource conflicts, or to ensure a clean execution environment. The subprocess will
	be created, run the function with the provided arguments, and return the result.

	Args:
		func           (Callable):     The function to execute in a subprocess.
			(SHOULD BE A TOP-LEVEL FUNCTION TO BE PICKLABLE)
		*args          (Any):          Positional arguments to pass to the function.
		timeout        (float | None): Maximum time in seconds to wait for the subprocess.
			If None, wait indefinitely. If the subprocess exceeds this time, it will be terminated.
		no_join        (bool):         If True, do not wait for the subprocess to finish (fire-and-forget).
		capture_output (bool):         If True, capture the subprocess' stdout/stderr and relay it
			in real time to the parent's stdout. This enables seeing print() output
			from the subprocess in the main process. (Defaults to False)
		**kwargs       (Any):          Keyword arguments to pass to the function.

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

	# Optionally setup output capture pipe and listener
	capturer: CaptureOutput | None = None
	if capture_output:
		capturer = CaptureOutput()

	# Create and start the subprocess using the module-level wrapper
	process: mp.Process = mp.Process(
		target=_subprocess_wrapper,
		args=(result_queue, func, args, kwargs),
		kwargs={"_capturer": capturer}
	)
	process.start()

	# For capture_output we must close the parent's copy of the write fd and start listener
	if capturer is not None:
		capturer.parent_close_write()
		capturer.start_listener()

	# Detach process if no_join (fire-and-forget)
	if result_queue is None:
		# If capturing, leave listener running in background (daemon)
		return None  # type: ignore

	# Use a single try/finally to ensure we always drain the listener once
	# and avoid repeating join calls in multiple branches.
	try:
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
			if not result_queue.empty():
				result_or_exception = result_queue.get_nowait()
				if isinstance(result_or_exception, Exception):
					raise result_or_exception
			raise RuntimeError(f"Subprocess failed with exit code {process.exitcode}")

		# Retrieve the result
		try:
			result_or_exception = result_queue.get_nowait()
			if isinstance(result_or_exception, Exception):
				raise result_or_exception
			return result_or_exception
		except Exception as e:
			raise RuntimeError("Subprocess did not return any result") from e
	finally:
		if capturer is not None:
			capturer.join_listener(timeout=5.0)


# "Private" function for subprocess wrapper (must be at module level for pickling on Windows)
def _subprocess_wrapper[R](
	result_queue: Any,
	func: Callable[..., R],
	args: tuple[Any, ...],
	kwargs: dict[str, Any],
	_capturer: CaptureOutput | None = None
) -> None:
	""" Wrapper function to execute the target function and store the result in the queue.

	Must be at module level to be pickable on Windows (spawn context).

	Args:
		result_queue (multiprocessing.Queue | None):  Queue to store the result or exception (None if detached).
		func         (Callable):                      The target function to execute.
		args         (tuple):                         Positional arguments for the function.
		kwargs       (dict):                          Keyword arguments for the function.
		_capturer    (CaptureOutput | None):          Optional CaptureOutput instance for stdout capture.
	"""
	try:
		# If a CaptureOutput instance was passed, redirect stdout/stderr to the pipe.
		if _capturer is not None:
			import sys
			writer = PipeWriter(_capturer.write_conn, _capturer.encoding, _capturer.errors)
			sys.stdout = writer
			sys.stderr = writer

		# Execute the target function and put the result in the queue
		result: R = func(*args, **kwargs)
		if result_queue is not None:
			result_queue.put(result)

	# Handle cleanup and exceptions
	except Exception as e:
		if result_queue is not None:
			result_queue.put(e)

