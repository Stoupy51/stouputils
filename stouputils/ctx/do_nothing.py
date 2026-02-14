
# Imports
from __future__ import annotations

from typing import Any

from .common import AbstractBothContextManager


# Context manager that does nothing
class DoNothing(AbstractBothContextManager["DoNothing"]):
	""" Context manager that does nothing.

	This is a no-op context manager that can be used as a placeholder
	or for conditional context management.

	Different from contextlib.nullcontext because it handles args and kwargs,
	along with **async** context management.

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

	def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
		""" Exit context manager (does nothing) """
		pass

	async def __aenter__(self) -> DoNothing:
		""" Enter async context manager (does nothing) """
		return self

	async def __aexit__(self, *excinfo: Any) -> None:
		""" Exit async context manager (does nothing) """
		pass

NullContextManager = DoNothing
""" Alias for DoNothing context manager """

