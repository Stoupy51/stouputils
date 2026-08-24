
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
import os
from contextlib import suppress
from typing import IO, Any


# Functions
def safe_close(file: IO[Any] | int | Any | None) -> None:
	""" Safely close a file object (or file descriptor) after flushing, ignoring any exceptions.

	Args:
		file (IO[Any] | int | None): The file object or file descriptor to close
	"""
	if isinstance(file, int):
		if file != -1:
			for func in (os.fsync, os.close):
				with suppress(Exception):
					func(file)
	elif file:
		for func in ("flush", "close"):
			with suppress(Exception):
				getattr(file, func)()

