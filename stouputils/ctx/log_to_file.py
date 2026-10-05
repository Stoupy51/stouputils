
# Imports
from __future__ import annotations

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

import os
import sys
from typing import IO, Any, TextIO

from ..io.path import super_open
from ..print.output_stream import TeeMultiOutput
from ..typing import CallableAny
from .common import AbstractBothContextManager


# Context manager to log to a file
class LogToFile(AbstractBothContextManager["LogToFile"]):
	""" Context manager to log to a file.

	This context manager allows you to temporarily log output to a file while still printing normally.
	The file will receive log messages without ANSI color codes.

	Args:
		path:            Path to the log file
		mode:            Mode to open the file in (default: "w")
		encoding:        Encoding to use for the file (default: "utf-8")
		tee_stdout:      Whether to redirect stdout to the file (default: True)
		tee_stderr:      Whether to redirect stderr to the file (default: True)
		ignore_lineup:   Whether the file receives what a terminal ends up showing (default: True):
			a progress bar once in its final state, and no line the cursor moves back to
		restore_on_exit: Whether to give stdout/stderr back on exit, when they still are the ones this context set (default: True)
	.. code-block:: python

		> import stouputils as stp
		> with stp.LogToFile("output.log"):
		>     stp.info("This will be logged to output.log and printed normally")
		>     print("This will also be logged")

		> with stp.LogToFile("output.log") as log_ctx:
		>     stp.warning("This will be logged to output.log and printed normally")
		>     log_ctx.change_file("new_file.log")
		>     print("This will be logged to new_file.log")
	"""
	def __init__(
		self,
		path: str,
		mode: str = "w",
		encoding: str = "utf-8",
		tee_stdout: bool = True,
		tee_stderr: bool = True,
		strip_colors: bool = False,
		ignore_lineup: bool = True,
		restore_on_exit: bool = True
	) -> None:
		self.path: str = path
		""" Attribute remembering path to the log file """
		self.mode: str = mode
		""" Attribute remembering mode to open the file in """
		self.encoding: str = encoding
		""" Attribute remembering encoding to use for the file """
		self.tee_stdout: bool = tee_stdout
		""" Whether to redirect stdout to the file """
		self.tee_stderr: bool = tee_stderr
		""" Whether to redirect stderr to the file """
		self.strip_colors: bool = strip_colors
		""" Whether to strip ANSI color codes from output sent to non-stdout/stderr files """
		self.ignore_lineup: bool = ignore_lineup
		""" Whether the file receives what a terminal ends up showing """
		self.restore_on_exit: bool = restore_on_exit
		""" Whether to give stdout/stderr back on exit, when they still are the ones this context set """
		self.file: IO[Any]
		""" Attribute remembering opened file """
		self.original_stdout: TextIO
		""" Original stdout before redirection """
		self.original_stderr: TextIO
		""" Original stderr before redirection """
		self.tees: dict[str, TeeMultiOutput] = {}
		""" The stream objects this context set, by the name of the ``sys`` attribute they replace """

	def __enter__(self) -> LogToFile:
		""" Enter context manager which opens the log file and redirects stdout/stderr """
		# Open file
		self.file = super_open(self.path, mode=self.mode, encoding=self.encoding)

		# Redirect stdout and stderr if requested
		self.original_stdout, self.original_stderr = sys.stdout, sys.stderr
		for name, wanted in (("stdout", self.tee_stdout), ("stderr", self.tee_stderr)):
			if wanted:
				tee = TeeMultiOutput(getattr(sys, name), self.file, strip_colors=self.strip_colors, ignore_lineup=self.ignore_lineup)
				self.tees[name] = tee
				setattr(sys, name, tee)
		return self

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager which closes the log file and restores stdout/stderr """
		self.close_file()
		if self.restore_on_exit:
			self.restore_streams()

	def close_file(self) -> None:
		""" Write the unfinished last lines, then close the file. """
		for tee in self.tees.values():
			tee.flush_pending()
		self.file.close()

	def restore_streams(self) -> None:
		""" Give back the streams this context replaced, leaving any that something else replaced since. """
		originals: dict[str, TextIO] = {"stdout": self.original_stdout, "stderr": self.original_stderr}
		for name, tee in self.tees.items():
			if getattr(sys, name) is tee:
				setattr(sys, name, originals[name])
		self.tees = {}

	async def __aenter__(self) -> LogToFile:
		""" Enter async context manager which opens the log file and redirects stdout/stderr """
		return self.__enter__()

	async def __aexit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit async context manager which closes the log file and restores stdout/stderr """
		self.__exit__(exc_type, exc_val, exc_tb)

	def change_file(self, new_path: str) -> None:
		""" Change the log file to a new path.

		Args:
			new_path: New path to the log file
		"""
		self.close_file()
		self.restore_streams()
		self.path = new_path
		self.__enter__()

	@staticmethod
	def common(
		logs_folder: str, filepath: str, func: CallableAny, init_kwargs: dict[str, Any] | None = None, *args: Any, **kwargs: Any,
	) -> Any:
		""" Common code used at the beginning of a program to launch main function

		Args:
			logs_folder: Folder to store logs in
			filepath:    Path to the main function
			func:        Main function to launch
			init_kwargs: Keyword arguments to pass to LogToFile constructor
			*args:       Arguments to pass to the main function
			**kwargs:    Keyword arguments to pass to the main function
		Returns:
			Return value of the main function
		>>> if __name__ == "__main__":
		...     LogToFile.common(f"{ROOT}/logs", __file__, main, init_kwargs={"strip_colors": True})
		"""
		# Import datetime
		from datetime import datetime

		# Build log file path
		if init_kwargs is None:
			init_kwargs = {}
		file_basename: str = os.path.splitext(os.path.basename(filepath))[0]
		date_time: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		date_str, time_str = date_time.split("_")
		log_filepath: str = f"{logs_folder}/{file_basename}/{date_str}/{time_str}.log"

		# Launch function with arguments if any
		with LogToFile(log_filepath, **init_kwargs):
			return func(*args, **kwargs)

