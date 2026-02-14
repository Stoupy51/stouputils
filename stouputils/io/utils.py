
# Imports
import os
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
				try:
					func(file)
				except Exception:
					pass
	elif file:
		for func in ("flush", "close"):
			try:
				getattr(file, func)()
			except Exception:
				pass

