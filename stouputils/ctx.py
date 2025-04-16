"""
This module provides context managers for temporarily silencing output.

- Muffle: Context manager that temporarily silences output (alternative to stouputils.decorators.silent())
- LogToFile: Context manager to log to a file every print call (with LINE_UP handling)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/ctx_module.gif
  :alt: stouputils ctx examples
"""

# Imports
import os
import sys
from collections.abc import Callable
from typing import IO, Any, TextIO

from .io import super_open
from .print import TeeMultiOutput


# Context manager to temporarily silence output
class Muffle:
	""" Context manager that temporarily silences output.

	Alternative to stouputils.decorators.silent()

	Examples:
		>>> with Muffle():
		...     print("This will not be printed")
	"""
	def __init__(self, mute_stderr: bool = False) -> None:
		self.mute_stderr: bool = mute_stderr
		""" Attribute remembering if stderr should be muted """
		self.original_stdout: TextIO = sys.stdout
		""" Attribute remembering original stdout """
		self.original_stderr: TextIO = sys.stderr
		""" Attribute remembering original stderr """

	def __enter__(self) -> None:
		""" Enter context manager which redirects stdout and stderr to devnull """
		# Redirect stdout to devnull
		sys.stdout = open(os.devnull, "w")

		# Redirect stderr to devnull if needed
		if self.mute_stderr:
			sys.stderr = open(os.devnull, "w")

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager which restores original stdout and stderr """
		# Restore original stdout
		sys.stdout.close()
		sys.stdout = self.original_stdout

		# Restore original stderr if needed
		if self.mute_stderr:
			sys.stderr.close()
			sys.stderr = self.original_stderr



# Context manager to log to a file
class LogToFile:
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

	Examples:
		.. code-block:: python

			> import stouputils as stp
			> with stp.LogToFile("output.log"):
			>     stp.info("This will be logged to output.log and printed normally")
			>     print("This will also be logged")
	"""
	def __init__(
		self,
		path: str,
		mode: str = "w",
		encoding: str = "utf-8",
		tee_stdout: bool = True,
		tee_stderr: bool = True,
		ignore_lineup: bool = True
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
		self.ignore_lineup: bool = ignore_lineup
		""" Whether to ignore lines containing LINE_UP escape sequence in files """
		self.file: IO[Any] = super_open(self.path, mode=self.mode, encoding=self.encoding)
		""" Attribute remembering opened file """
		self.original_stdout: TextIO = sys.stdout
		""" Original stdout before redirection """
		self.original_stderr: TextIO = sys.stderr
		""" Original stderr before redirection """

	def __enter__(self) -> None:
		""" Enter context manager which opens the log file and redirects stdout/stderr """
		# Redirect stdout and stderr if requested
		if self.tee_stdout:
			sys.stdout = TeeMultiOutput(self.original_stdout, self.file, ignore_lineup=self.ignore_lineup)

		if self.tee_stderr:
			sys.stderr = TeeMultiOutput(self.original_stderr, self.file, ignore_lineup=self.ignore_lineup)

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager which closes the log file and restores stdout/stderr """
		# Restore original stdout and stderr
		if self.tee_stdout:
			sys.stdout = self.original_stdout

		if self.tee_stderr:
			sys.stderr = self.original_stderr

		# Close file
		self.file.close()

	@staticmethod
	def common(logs_folder: str, filepath: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
		""" Common code used at the beginning of a program to launch main function

		Args:
			logs_folder (str): Folder to store logs in
			filepath    (str): Path to the main function
			func        (Callable[..., Any]): Main function to launch
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

