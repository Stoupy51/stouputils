"""
This module provides context managers for temporarily silencing output.

- Muffle: Context manager that temporarily silences output (alternative to stouputils.decorators.silent())
- LogToFile: Context manager to log to a file every print call (with LINE_UP handling)

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/ctx_module.gif
  :alt: stouputils ctx examples
"""

# Imports
from __future__ import annotations
import os
import sys
import time
from collections.abc import Callable
from typing import IO, Any, TextIO

from .io import super_open
from .print import TeeMultiOutput, debug


# Context manager that does nothing
class DoNothing:
	""" Context manager that does nothing.

	This is a no-op context manager that can be used as a placeholder
	or for conditional context management.

	Examples:
		>>> with DoNothing():
		...     print("This will be printed normally")
		This will be printed normally

		>>> # Conditional context management
		>>> some_condition = True
		>>> ctx = DoNothing() if some_condition else Muffle()
		>>> with ctx:
		...     print("May or may not be printed depending on condition")
		May or may not be printed depending on condition
	"""
	def __init__(self, *args: Any, **kwargs: Any) -> None:
		""" No initialization needed, this is a no-op context manager """
		pass

	def __enter__(self) -> DoNothing:
		""" Enter context manager (does nothing) """
		return self

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager (does nothing) """
		pass


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

	def __enter__(self) -> Muffle:
		""" Enter context manager which redirects stdout and stderr to devnull """
		# Redirect stdout to devnull
		sys.stdout = open(os.devnull, "w", encoding="utf-8")

		# Redirect stderr to devnull if needed
		if self.mute_stderr:
			sys.stderr = open(os.devnull, "w", encoding="utf-8")

		# Return self
		return self

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

	def __enter__(self) -> LogToFile:
		""" Enter context manager which opens the log file and redirects stdout/stderr """
		# Redirect stdout and stderr if requested
		if self.tee_stdout:
			sys.stdout = TeeMultiOutput(self.original_stdout, self.file, ignore_lineup=self.ignore_lineup)
		if self.tee_stderr:
			sys.stderr = TeeMultiOutput(self.original_stderr, self.file, ignore_lineup=self.ignore_lineup)

		# Return self
		return self

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


# Context manager to measure execution time
class MeasureTime:
	""" Context manager to measure execution time.

	This context manager measures the execution time of the code block it wraps
	and prints the result using a specified print function.

	Args:
		print_func      (Callable): Function to use to print the execution time (e.g. debug, info, warning, error, etc.).
		message         (str):      Message to display with the execution time. Defaults to "Execution time".
		perf_counter    (bool):     Whether to use time.perf_counter_ns or time.time_ns. Defaults to True.

	Examples:
		.. code-block:: python

			> import time
			> import stouputils as stp
			> with stp.MeasureTime(stp.info, message="My operation"):
			...     time.sleep(0.5)
			> # [INFO HH:MM:SS] My operation: 500.123ms (500123456ns)

			> with stp.MeasureTime(): # Uses debug by default
			...     time.sleep(0.1)
			> # [DEBUG HH:MM:SS] Execution time: 100.456ms (100456789ns)
	"""
	def __init__(
		self,
		print_func: Callable[..., None] = debug,
		message: str = "Execution time",
		perf_counter: bool = True
	) -> None:
		self.print_func: Callable[..., None] = print_func
		""" Function to use for printing the execution time """
		self.message: str = message
		""" Message to display with the execution time """
		self.perf_counter: bool = perf_counter
		""" Whether to use time.perf_counter_ns or time.time_ns """
		self.ns: Callable[[], int] = time.perf_counter_ns if perf_counter else time.time_ns
		""" Time function to use """
		self.start_ns: int = 0
		""" Start time in nanoseconds """

	def __enter__(self) -> MeasureTime:
		""" Enter context manager, record start time """
		self.start_ns = self.ns()
		return self

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit context manager, calculate duration and print """
		# Measure the execution time (nanoseconds and seconds)
		total_ns: int = self.ns() - self.start_ns
		total_ms: float = total_ns / 1_000_000
		total_s: float = total_ns / 1_000_000_000

		# Print the execution time (nanoseconds if less than 0.1s, seconds otherwise)
		if total_ms < 100:
			self.print_func(f"{self.message}: {total_ms:.3f}ms ({total_ns}ns)")
		elif total_s < 60:
			self.print_func(f"{self.message}: {(total_s):.5f}s")
		else:
			minutes: int = int(total_s) // 60
			seconds: int = int(total_s) % 60
			if minutes < 60:
				self.print_func(f"{self.message}: {minutes}m {seconds}s")
			else:
				hours: int = minutes // 60
				minutes: int = minutes % 60
				if hours < 24:
					self.print_func(f"{self.message}: {hours}h {minutes}m {seconds}s")
				else:
					days: int = hours // 24
					hours: int = hours % 24
					self.print_func(f"{self.message}: {days}d {hours}h {minutes}m {seconds}s")

