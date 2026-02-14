
# Imports
from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from ..print.message import debug
from .common import AbstractBothContextManager


# Context manager to measure execution time
class MeasureTime(AbstractBothContextManager["MeasureTime"]):
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

	async def __aenter__(self) -> MeasureTime:
		""" Enter async context manager, record start time """
		return self.__enter__()

	async def __aexit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit async context manager, calculate duration and print """
		self.__exit__(exc_type, exc_val, exc_tb)

