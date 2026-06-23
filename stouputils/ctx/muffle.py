
# Imports
from __future__ import annotations

import io
import logging
import os
import sys
from collections.abc import Sequence
from typing import IO, Any

from .common import AbstractBothContextManager


# Logging handler used to detect error-level records while muffling
class ErrorLevelDetector(logging.Handler):
	""" Logging handler that only remembers whether a record at/above its level was emitted.

	Used by :py:class:`Muffle` to decide whether captured output should be replayed,
	since some libraries log their failures instead of raising.
	"""
	def __init__(self, level: int) -> None:
		super().__init__(level=level)
		self.triggered: bool = False
		""" Whether a record at/above the configured level has been seen """

	def emit(self, record: logging.LogRecord) -> None:
		if record.levelno >= self.level:
			self.triggered = True


# Context manager to temporarily silence output
class Muffle(AbstractBothContextManager["Muffle"]):
	""" Context manager that temporarily silences output.
	(No thread-safety guaranteed)

	Alternative to :py:deco:`~stouputils.decorators.silent`

	By default the output is sent to devnull and lost. When ``replay_on_error`` is enabled,
	the output is captured in memory instead and only written back to the original stream if
	an error occurs inside the block. An "error" is either an exception propagating out of the
	block, or - when ``error_log_level`` is set - any logging record at/above that level emitted
	by the watched loggers (handy for libraries that log their failures instead of raising).

	Args:
		mute_stderr		(bool):						Whether to mute stderr as well as stdout
		replay_on_error	(bool):						Capture output in memory and replay it if an error occurs
		error_log_level	(int | None):				Also treat log records at/above this level as an error (e.g. ``logging.ERROR``)
		watch_loggers	(Sequence[str] | None):		Names of the loggers to watch for ``error_log_level`` (default: root logger only)

	Examples:
		>>> with Muffle():
		...     print("This will not be printed")

		>>> # Replays the captured output because an exception escapes the block
		>>> try:
		...     with Muffle(replay_on_error=True):
		...         print("Context that explains the failure below")
		...         raise ValueError("boom")
		... except ValueError:
		...     pass
		Context that explains the failure below

		>>> # Stays silent because nothing went wrong
		>>> import logging
		>>> with Muffle(replay_on_error=True, error_log_level=logging.ERROR):
		...     print("This will not be printed")
	"""
	def __init__(
		self,
		mute_stderr: bool = False,
		replay_on_error: bool = False,
		error_log_level: int | None = None,
		watch_loggers: Sequence[str] | None = None,
	) -> None:
		self.mute_stderr: bool = mute_stderr
		""" Attribute remembering if stderr should be muted """
		self.replay_on_error: bool = replay_on_error
		""" Attribute remembering if captured output should be replayed on error """
		self.error_log_level: int | None = error_log_level
		""" Attribute remembering the logging level that counts as an error (if any) """
		self.watch_loggers: Sequence[str] | None = watch_loggers
		""" Attribute remembering which loggers to watch for error records """
		self.original_stdout: IO[Any]
		""" Attribute remembering original stdout """
		self.original_stderr: IO[Any]
		""" Attribute remembering original stderr """
		self._buffer: io.StringIO | None = None
		""" In-memory buffer holding captured output when replay_on_error is enabled """
		self._detector: ErrorLevelDetector | None = None
		""" Logging handler watching for error-level records """
		self._watched: list[logging.Logger] = []
		""" Loggers the detector is currently attached to """

	def __enter__(self) -> Muffle:
		""" Enter context manager which redirects stdout (and optionally stderr) to a sink """
		self.original_stdout = sys.stdout

		# Pick the sink: an in-memory buffer (to allow replay) or devnull (output is lost)
		if self.replay_on_error:
			self._buffer = io.StringIO()
			sys.stdout = self._buffer
			if self.mute_stderr:
				self.original_stderr = sys.stderr
				sys.stderr = self._buffer	# Shared buffer so stdout/stderr ordering is preserved

			# Optionally watch loggers so output is also replayed when a failure is only logged
			if self.error_log_level is not None:
				self._detector = ErrorLevelDetector(self.error_log_level)
				names: list[str] = list(self.watch_loggers) if self.watch_loggers is not None else [""]
				self._watched = [logging.getLogger(name) for name in names]
				for logger in self._watched:
					logger.addHandler(self._detector)
		else:
			sys.stdout = open(os.devnull, "w", encoding="utf-8")
			if self.mute_stderr:
				self.original_stderr = sys.stderr
				sys.stderr = open(os.devnull, "w", encoding="utf-8")

		# Return self
		return self

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager which restores original streams (and replays output on error) """
		# Detach the logging detector first
		had_log_error: bool = False
		if self._detector is not None:
			had_log_error = self._detector.triggered
			for logger in self._watched:
				logger.removeHandler(self._detector)
		self._watched = []
		self._detector = None

		if self.replay_on_error:
			# Grab the captured output, then restore the original streams
			captured: str = self._buffer.getvalue() if self._buffer is not None else ""
			if self.mute_stderr:
				sys.stderr = self.original_stderr
			sys.stdout = self.original_stdout
			if self._buffer is not None:
				self._buffer.close()
				self._buffer = None

			# Replay only when something went wrong (exception propagating or error logged)
			if (exc_type is not None or had_log_error) and captured:
				self.write_safely(self.original_stdout, captured)
		else:
			# Restore original stdout
			sys.stdout.close()
			sys.stdout = self.original_stdout

			# Restore original stderr if needed
			if self.mute_stderr:
				sys.stderr.close()
				sys.stderr = self.original_stderr

	@staticmethod
	def write_safely(stream: IO[Any], text: str) -> None:
		""" Write text to a stream, replacing characters the stream's encoding cannot represent.

		Captured output may contain unicode (e.g. Rich panels) that a narrow console encoding
		(such as cp1252 on Windows) cannot encode, which would otherwise raise UnicodeEncodeError.
		"""
		encoding: str = getattr(stream, "encoding", None) or "utf-8"
		stream.write(text.encode(encoding, errors="replace").decode(encoding, errors="replace"))
		stream.flush()

	async def __aenter__(self) -> Muffle:
		""" Enter async context manager which redirects stdout and stderr to devnull """
		return self.__enter__()

	async def __aexit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit async context manager which restores original stdout and stderr """
		self.__exit__(exc_type, exc_val, exc_tb)

