
# Imports
import os
import sys
from typing import TextIO, Any

# Context manager to temporarily silence output
class Muffle:
	""" Context manager that temporarily silences output.\n
	Alternative to stouputils.decorators.silent()
	
	>>> with Muffle():
	...     print("This will not be printed")
	"""
	def __init__(self, mute_stderr: bool = False) -> None:
		self.mute_stderr: bool = mute_stderr

	def __enter__(self) -> None:
		self.original_stdout: TextIO = sys.stdout
		sys.stdout = open(os.devnull, 'w')
		if self.mute_stderr:
			self.original_stderr: TextIO = sys.stderr
			sys.stderr = open(os.devnull, 'w')

	def __exit__(self, exc_type: type[BaseException]|None, exc_val: BaseException|None, exc_tb: Any|None) -> None:
		sys.stdout.close()
		sys.stdout = self.original_stdout
		if self.mute_stderr:
			sys.stderr.close()
			sys.stderr = self.original_stderr


