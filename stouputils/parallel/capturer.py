
# Imports
import os
from typing import IO, Any

from ..io import safe_close


class PipeWriter:
	""" A writer that sends data to a multiprocessing Connection. """
	def __init__(self, conn: Any, encoding: str, errors: str):
		self.conn: Any = conn
		self.encoding: str = encoding
		self.errors: str = errors

	def write(self, data: str) -> int:
		self.conn.send_bytes(data.encode(self.encoding, errors=self.errors))
		return len(data)

	def flush(self) -> None:
		pass


class CaptureOutput:
	""" Utility to capture stdout/stderr from a subprocess and relay it to the parent's stdout.

	The class creates an os.pipe(), marks fds as inheritable (for spawn method),
	provides methods to start a listener thread that reads from the pipe and writes
	to the main process's sys.stdout/sys.stderr, and to close/join the listener.
	"""
	def __init__(self, encoding: str = "utf-8", errors: str = "replace"):
		import multiprocessing as mp
		import threading
		self.encoding: str = encoding
		self.errors: str = errors
		self.read_conn, self.write_conn = mp.Pipe(duplex=False)
		self.read_fd = self.read_conn.fileno()
		self.write_fd = self.write_conn.fileno()
		# Internal state for the listener thread and reader handle
		self._thread: threading.Thread | None = None
		self._reader_file: IO[Any] | None = None
		# Sentinel string that will terminate the listener when seen in the stream
		try:
			os.set_inheritable(self.read_fd, True)
			os.set_inheritable(self.write_fd, True)
		except Exception:
			pass

	def __repr__(self) -> str:
		return f"<CaptureOutput read_fd={self.read_fd} write_fd={self.write_fd}>"

	# Pickle support: exclude unpicklable attributes
	def __getstate__(self) -> dict[str, Any]:
		state = self.__dict__.copy()
		state["_thread"] = None
		return state

	def redirect(self) -> None:
		""" Redirect sys.stdout and sys.stderr to the pipe's write end. """
		import sys
		writer = PipeWriter(self.write_conn, self.encoding, self.errors)
		sys.stdout = writer
		sys.stderr = writer

	def parent_close_write(self) -> None:
		""" Close the parent's copy of the write end; the child's copy remains. """
		safe_close(self.write_conn)
		self.write_fd = -1	# Prevent accidental reuse

	def start_listener(self) -> None:
		""" Start a daemon thread that forwards data from the pipe to sys.stdout/sys.stderr. """
		import sys
		if self._thread is not None:
			return

		# Handler function for reading from the pipe
		buffer: str = ""
		def _handle_buffer() -> None:
			nonlocal buffer
			if buffer:
				try:
					sys.stdout.write(buffer)
					sys.stdout.flush()
				except Exception:
					pass
				buffer = ""

		# Thread target function
		def _reader() -> None:
			nonlocal buffer
			try:
				while True:
					# Read the next message from the pipe. Use recv_bytes() without a maxlength
					# so we don't error when a single message is larger than our chunk size.
					try:
						data: bytes = self.read_conn.recv_bytes()
					except (EOFError, OSError, BrokenPipeError):
						_handle_buffer()
						break

					# Decode bytes to text & append to buffer
					try:
						chunk: str = data.decode(self.encoding, errors=self.errors)
					except Exception:
						chunk = data.decode(self.encoding, errors="replace")
					buffer += chunk
			finally:
				safe_close(self.read_conn)
				self.read_fd = -1
				self._thread = None		# Mark thread as stopped so callers don't block unnecessarily

		# Start the listener thread
		import threading
		self._thread = threading.Thread(target=_reader, daemon=True)
		self._thread.start()

	def join_listener(self, timeout: float | None = None) -> None:
		""" Wait for the listener thread to finish (until EOF). """
		if self._thread is None:
			safe_close(self.read_conn)
			self.read_fd = -1
			return
		self._thread.join(timeout)

		# If thread finished, ensure read fd is closed and clear thread
		if self._thread and not self._thread.is_alive():
			self._thread = None

