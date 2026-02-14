
# Imports
from __future__ import annotations

from typing import Any

from .common import AbstractBothContextManager


# Context manager to temporarily set multiprocessing start method
class SetMPStartMethod(AbstractBothContextManager["SetMPStartMethod"]):
	""" Context manager to temporarily set multiprocessing start method.

	This context manager allows you to temporarily change the multiprocessing start method
	and automatically restores the original method when exiting the context.

	Args:
		start_method (str): The start method to use: "spawn", "fork", or "forkserver"

	Examples:
		.. code-block:: python

			> import multiprocessing as mp
			> import stouputils as stp
			> # Temporarily use spawn method
			> with stp.SetMPStartMethod("spawn"):
			> ...     # Your multiprocessing code here
			> ...     pass

			> # Original method is automatically restored
	"""
	def __init__(self, start_method: str | None) -> None:
		self.start_method: str | None = start_method
		""" The start method to use """
		self.old_method: str | None = None
		""" The original start method to restore """

	def __enter__(self) -> SetMPStartMethod:
		""" Enter context manager which sets the start method """
		if self.start_method is None:
			return self
		import multiprocessing as mp

		self.old_method = mp.get_start_method(allow_none=True)
		if self.old_method != self.start_method:
			mp.set_start_method(self.start_method, force=True)
		return self

	def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
		""" Exit context manager which restores the original start method """
		if self.start_method is None:
			return
		import multiprocessing as mp

		if self.old_method != self.start_method:
			mp.set_start_method(self.old_method, force=True)

	async def __aenter__(self) -> SetMPStartMethod:
		""" Enter async context manager which sets the start method """
		return self.__enter__()

	async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
		""" Exit async context manager which restores the original start method """
		self.__exit__(exc_type, exc_val, exc_tb)

