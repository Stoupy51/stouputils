
# Imports
from __future__ import annotations

import os
import sys
from typing import IO, Any

from .common import AbstractBothContextManager


# Context manager to temporarily silence output
class Muffle(AbstractBothContextManager["Muffle"]):
	""" Context manager that temporarily silences output.
	(No thread-safety guaranteed)

	Alternative to :py:deco:`~stouputils.decorators.silent`

	Examples:
		>>> with Muffle():
		...     print("This will not be printed")
	"""
	def __init__(self, mute_stderr: bool = False) -> None:
		self.mute_stderr: bool = mute_stderr
		""" Attribute remembering if stderr should be muted """
		self.original_stdout: IO[Any]
		""" Attribute remembering original stdout """
		self.original_stderr: IO[Any]
		""" Attribute remembering original stderr """

	def __enter__(self) -> Muffle:
		""" Enter context manager which redirects stdout and stderr to devnull """
		# Redirect stdout to devnull
		self.original_stdout = sys.stdout
		sys.stdout = open(os.devnull, "w", encoding="utf-8")

		# Redirect stderr to devnull if needed
		if self.mute_stderr:
			self.original_stderr = sys.stderr
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

	async def __aenter__(self) -> Muffle:
		""" Enter async context manager which redirects stdout and stderr to devnull """
		return self.__enter__()

	async def __aexit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		""" Exit async context manager which restores original stdout and stderr """
		self.__exit__(exc_type, exc_val, exc_tb)

