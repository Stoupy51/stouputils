
# Imports
from __future__ import annotations

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
		path (str): Path to the log file
		mode (str): Mode to open the file in (default: "w")
		encoding (str): Encoding to use for the file (default: "utf-8")
		tee_stdout (bool): Whether to redirect stdout to the file (default: True)
		tee_stderr (bool): Whether to redirect stderr to the file (default: True)
		ignore_lineup (bool): Whether to ignore lines containing LINE_UP escape sequence in files (default: False)
		restore_on_exit (bool): Whether to restore original stdout/stderr on exit (default: False)
			This ctx uses :py:class:`~stouputils.print.TeeMultiOutput` which handles closed files gracefully, so restoring is not mandatory.

	Examples:
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
		strip_colors: bool = True,
		ignore_lineup: bool = True,
		restore_on_exit: bool = False
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
		""" Whether to ignore lines containing LINE_UP escape sequence in files """
		self.restore_on_exit: bool = restore_on_exit
		""" Whether to restore original stdout/stderr on exit.
		This ctx uses :py:class:`~stouputils.print.TeeMultiOutput` which handles closed files gracefully, so restoring is not mandatory. """
		self.file: IO[Any]
		""" Attribute remembering opened file """
		self.original_stdout: TextIO
		""" Original stdout before redirection """
		self.original_stderr: TextIO
		""" Original stderr before redirection """

	def __enter__(self) -> LogToFile:
		""" Enter context manager which opens the log file and redirects stdout/stderr """
		# Open file
		self.file = super_open(self.path, mode=self.mode, encoding=self.encoding)

		# Redirect stdout and stderr if requested
		if self.tee_stdout:
			self.original_stdout = sys.stdout
			sys.stdout = TeeMultiOutput(self.original_stdout, self.file, strip_colors=self.strip_colors, ignore_lineup=self.ignore_lineup)
		if self.tee_stderr:
			self.original_stderr = sys.stderr
			sys.stderr = TeeMultiOutput(self.original_stderr, self.file, strip_colors=self.strip_colors, ignore_lineup=self.ignore_lineup)

		# Return self
		return self

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager which closes the log file and restores stdout/stderr """
		# Restore original stdout and stderr (if requested)
		if self.restore_on_exit:
			if self.tee_stdout:
				sys.stdout = self.original_stdout
			if self.tee_stderr:
				sys.stderr = self.original_stderr

		# Close file
		self.file.close()

	async def __aenter__(self) -> LogToFile:
		""" Enter async context manager which opens the log file and redirects stdout/stderr """
		return self.__enter__()

	async def __aexit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit async context manager which closes the log file and restores stdout/stderr """
		self.__exit__(exc_type, exc_val, exc_tb)

	def change_file(self, new_path: str) -> None:
		""" Change the log file to a new path.

		Args:
			new_path (str): New path to the log file
		"""
		# Close current file, open new file and redirect outputs
		self.file.close()
		self.path = new_path
		self.__enter__()

	@staticmethod
	def common(logs_folder: str, filepath: str, func: CallableAny, *args: Any, **kwargs: Any) -> Any:
		""" Common code used at the beginning of a program to launch main function

		Args:
			logs_folder (str): Folder to store logs in
			filepath    (str): Path to the main function
			func        (CallableAny): Main function to launch
			*args       (tuple[Any, ...]): Arguments to pass to the main function
			**kwargs    (dict[str, Any]): Keyword arguments to pass to the main function
		Returns:
			Any: Return value of the main function

		Examples:
			>>> if __name__ == "__main__":
			...     LogToFile.common(f"{ROOT}/logs", __file__, main)
		"""
		# Import datetime
		from datetime import datetime

		# Build log file path
		file_basename: str = os.path.splitext(os.path.basename(filepath))[0]
		date_time: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
		date_str, time_str = date_time.split("_")
		log_filepath: str = f"{logs_folder}/{file_basename}/{date_str}/{time_str}.log"

		# Launch function with arguments if any
		with LogToFile(log_filepath):
			return func(*args, **kwargs)

