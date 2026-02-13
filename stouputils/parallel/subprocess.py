
# Imports
import time
from collections.abc import Callable
from typing import Any

from ..typing import JsonDict
from .capturer import CaptureOutput
from .common import resolve_process_title


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
	process_title: str | None = None,
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
		process_title  (str | None):   If provided, sets the process title visible in process lists.
			If it starts with '+++', this prefix is replaced by the current process title.
		**kwargs       (Any):          Keyword arguments to pass to the function.

	Returns:
		R: The return value of the function.

	Raises:
		:py:exc:`RemoteSubprocessError`: If the child raised an exception - contains the child's formatted traceback.
		:py:exc:`RuntimeError`: If the subprocess exits with a non-zero exit code or did not return a result.
		:py:exc:`TimeoutError`: If the subprocess exceeds the specified timeout.

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
			> run_in_subprocess(some_gpu_func, data, timeout=300.0, process_title="+++_gpu_worker")
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
		kwargs={"capturer": capturer, "process_title": resolve_process_title(process_title)}
	)
	process.start()

	# Function to kill the process safely
	def kill_process_tree() -> None:
		if not process.is_alive():
			return
		process.terminate()
		time.sleep(0.5)
		if process.is_alive():
			import psutil
			proc = psutil.Process(process.pid)
			procs = [proc, *proc.children(recursive=True)]
			for p in procs:
				try:
					p.terminate()
				except Exception:
					pass
			_, alive = psutil.wait_procs(procs, timeout=3)
			for p in alive:
				try:
					p.kill()
				except Exception:
					pass
		process.join()

	# For capture_output we must close the parent's copy of the write fd and start listener
	if capturer is not None:
		capturer.parent_close_write()
		capturer.start_listener()

	# Detach process if no_join (fire-and-forget)
	if result_queue is None:
		# If capturing, leave listener running in background (daemon)
		return process  # type: ignore

	# Wait for result with short polling intervals to catch KeyboardInterrupt quickly
	try:
		try:
			import queue
			start_time = time.time()
			while True:
				try:
					result_payload: JsonDict = result_queue.get(timeout=0.1)
					break
				except queue.Empty as e:
					if timeout is not None and (time.time() - start_time) >= timeout:
						raise TimeoutError(f"Subprocess exceeded timeout of {timeout} seconds and was terminated") from e
					if not process.is_alive():
						process.join()
						raise RuntimeError(f"Subprocess terminated unexpectedly with exit code {process.exitcode}") from e
		except KeyboardInterrupt:
			raise
		finally:
			# Give the child a short grace period to exit cleanly and run atexit
			# handlers (which unlink semaphores). Without this, kill_process_tree()
			# terminates the child during cleanup, leaking semaphores.
			if process.is_alive():
				process.join(timeout=2.0)
			kill_process_tree()

		# If the child sent a structured exception, raise it with the formatted traceback
		if result_payload.pop("ok", False) is False:
			raise RemoteSubprocessError(**result_payload)
		return result_payload["result"]

	# Finally, clean up queue resources and drain/join the listener
	finally:
		try:
			result_queue.cancel_join_thread()
			result_queue.close()
		except Exception:
			pass
		if capturer is not None:
			capturer.join_listener(timeout=5.0)


# "Private" function for subprocess wrapper (must be at module level for pickling on Windows)
def _subprocess_wrapper[R](
	result_queue: Any | None,
	func: Callable[..., R],
	args: tuple[Any, ...],
	kwargs: dict[str, Any],
	capturer: CaptureOutput | None = None,
	process_title: str | None = None
) -> None:
	""" Wrapper function to execute the target function and store the result in the queue.

	Must be at module level to be pickable on Windows (spawn context).

	Args:
		result_queue (multiprocessing.Queue | None):  Queue to store the result or exception (None if detached).
		func         (Callable):                      The target function to execute.
		args         (tuple):                         Positional arguments for the function.
		kwargs       (dict):                          Keyword arguments for the function.
		capturer     (CaptureOutput | None):          Optional CaptureOutput instance for stdout capture.
		process_title (str | None):                   Optional process title to set.
	"""
	try:
		# Set process title if provided
		if process_title is not None:
			import setproctitle
			setproctitle.setproctitle(process_title)

		# If a CaptureOutput instance was passed, redirect stdout/stderr to the pipe.
		if capturer is not None:
			capturer.redirect()

		# Execute the target function and put the result in the queue
		result: R = func(*args, **kwargs)
		if result_queue is not None:
			# Use timeout to prevent blocking if parent is no longer listening
			try:
				result_queue.put({"ok": True, "result": result}, timeout=5.0)
			except Exception:
				pass  # Parent likely terminated, just exit

	# Handle KeyboardInterrupt specially - don't try to send it back, just exit
	except KeyboardInterrupt:
		# Exit immediately without trying to communicate with parent
		pass

	# Handle cleanup and exceptions
	except Exception as e:
		if result_queue is not None:
			try:
				import traceback
				tb = traceback.format_exc()
				# Use timeout to prevent blocking if parent is no longer listening
				result_queue.put({
					"ok": False,
					"exc_type": e.__class__.__name__,
					"exc_repr": repr(e),
					"traceback_str": tb,
				}, timeout=5.0)
			except Exception:
				# Nothing we can do if even this fails
				pass

	finally:
		# Clean up queue to release its internal semaphores
		if result_queue is not None:
			try:
				result_queue.close()
				result_queue.join_thread()
			except Exception:
				pass

		# Restore stdout/stderr and close capturer write end
		if capturer is not None:
			capturer.child_close()  # Close child's copy of the write end

