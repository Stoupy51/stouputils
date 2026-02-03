
# Imports
import time
from collections.abc import Callable
from typing import Any

from ..typing import JsonDict
from .capturer import CaptureOutput


class RemoteSubprocessError(RuntimeError):
	""" Raised in the parent when the child raised an exception - contains the child's formatted traceback. """
	def __init__(self, exc_type: str, exc_repr: str, traceback_str: str):
		msg = f"Exception in subprocess ({exc_type}): {exc_repr}\n\nRemote traceback:\n{traceback_str}"
		super().__init__(msg)
		self.remote_type = exc_type
		self.remote_repr = exc_repr
		self.remote_traceback = traceback_str


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
		no_join        (bool):         If True, do not wait for the subprocess to finish (fire-and-forget) and return the Process object.
		capture_output (bool):         If True, capture the subprocess' stdout/stderr and relay it
			in real time to the parent's stdout. This enables seeing print() output
			from the subprocess in the main process.
		**kwargs       (Any):          Keyword arguments to pass to the function.

	Returns:
		R: The return value of the function.

	Raises:
		RemoteSubprocessError: If the child raised an exception - contains the child's formatted traceback.
		RuntimeError: If the subprocess exits with a non-zero exit code or did not return a result.
		TimeoutError: If the subprocess exceeds the specified timeout.

	Examples:
		.. code-block:: python

			> # Simple function execution
			> run_in_subprocess(doctest_square, 5)
			25

			> # Function with multiple arguments
			> def add(a: int, b: int, c: int) -> int:
			.     return a + b + c
			> run_in_subprocess(add, 10, 20, c=30)
			60

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
	result_queue: Queue[JsonDict] | None = None if no_join else Queue()

	# Optionally setup output capture pipe and listener
	capturer: CaptureOutput | None = None
	if capture_output:
		capturer = CaptureOutput()

	# Create and start the subprocess using the module-level wrapper
	process: mp.Process = mp.Process(
		target=_subprocess_wrapper,
		args=(result_queue, func, args, kwargs),
		kwargs={"capturer": capturer}
	)
	process.start()

	# Function to kill the process safely
	def kill_process() -> None:
		if process.is_alive():
			process.terminate()
			time.sleep(0.5)
			if process.is_alive():
				process.kill()
			process.join()

	# For capture_output we must close the parent's copy of the write fd and start listener
	if capturer is not None:
		capturer.parent_close_write()
		capturer.start_listener()

	# Detach process if no_join (fire-and-forget)
	if result_queue is None:
		# If capturing, leave listener running in background (daemon)
		return process  # type: ignore

	# Use a single try/finally to ensure we always drain the listener once
	# and avoid repeating join calls in multiple branches.
	try:
		try:
			result_payload: JsonDict = result_queue.get(timeout=timeout)
		except Exception as e:
			# Queue.get timed out or failed
			raise TimeoutError(f"Subprocess exceeded timeout of {timeout} seconds and was terminated") from e
		finally:
			kill_process()

		# If the child sent a structured exception, raise it with the formatted traceback
		if result_payload.pop("ok", False) is False:
			raise RemoteSubprocessError(**result_payload)
		else:
			return result_payload["result"]

	# Finally, ensure we drain/join the listener if capturing output
	finally:
		if capturer is not None:
			capturer.join_listener(timeout=5.0)


# "Private" function for subprocess wrapper (must be at module level for pickling on Windows)
def _subprocess_wrapper[R](
	result_queue: Any,
	func: Callable[..., R],
	args: tuple[Any, ...],
	kwargs: dict[str, Any],
	capturer: CaptureOutput | None = None
) -> None:
	""" Wrapper function to execute the target function and store the result in the queue.

	Must be at module level to be pickable on Windows (spawn context).

	Args:
		result_queue (multiprocessing.Queue | None):  Queue to store the result or exception (None if detached).
		func         (Callable):                      The target function to execute.
		args         (tuple):                         Positional arguments for the function.
		kwargs       (dict):                          Keyword arguments for the function.
		capturer     (CaptureOutput | None):          Optional CaptureOutput instance for stdout capture.
	"""
	try:
		# If a CaptureOutput instance was passed, redirect stdout/stderr to the pipe.
		if capturer is not None:
			capturer.redirect()

		# Execute the target function and put the result in the queue
		result: R = func(*args, **kwargs)
		if result_queue is not None:
			result_queue.put({"ok": True, "result": result})

	# Handle cleanup and exceptions
	except Exception as e:
		if result_queue is not None:
			try:
				import traceback
				tb = traceback.format_exc()
				result_queue.put({
					"ok": False,
					"exc_type": e.__class__.__name__,
					"exc_repr": repr(e),
					"traceback_str": tb,
				})
			except Exception:
				# Nothing we can do if even this fails
				pass

