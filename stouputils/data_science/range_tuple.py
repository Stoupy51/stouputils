"""
This module contains the RangeTuple class, which provides a named tuple for range parameters.

This class contains methods for:

- Iterating over range values
- Accessing range values by index
- Slicing range values
- Converting to string representation
"""

# Imports
from __future__ import annotations

from collections.abc import Iterator
from typing import NamedTuple

import numpy as np

def safe_divide_none(a: float | None, b: float | None) -> float | None:
	""" Safe division of two numbers, return None if either number is None or denominator is 0.

	Args:
		a	(float | None):	First number
		b	(float | None):	Second number
	Returns:
		float | None:	Result of the division or None if denominator is None

	Examples:
		>>> None == safe_divide_none(None, 2)
		True
		>>> None == safe_divide_none(10, None)
		True
		>>> None == safe_divide_none(10, 0)
		True
		>>> safe_divide_none(10, 2)
		5.0
	"""
	return a / b if a is not None and b is not None and b > 0 else None

def safe_multiply_none(a: float | None, b: float | None) -> float | None:
	""" Safe multiplication of two numbers, return None if either number is None.

	Args:
		a	(float | None):	First number
		b	(float | None):	Second number
	Returns:
		float | None:	Result of the multiplication or None if either number is None

	Examples:
		>>> None == safe_multiply_none(None, 2)
		True
		>>> None == safe_multiply_none(10, None)
		True
		>>> safe_multiply_none(10, 2)
		20
		>>> safe_multiply_none(-10, 2)
		-20
	"""
	return a * b if a is not None and b is not None else None

# Create base tuple class
class _RangeTupleBase(NamedTuple):
	""" Base class for RangeTuple """
	mini: float | None
	""" The minimum value (inclusive) (can be None if default is set) """
	maxi: float | None
	""" The maximum value (exclusive) (can be None if default is set) """
	step: float | None
	""" The step value between elements (can be None if default is set) """
	default: float | None
	""" Optional default value, usually middle of range """


# Tuple class for range parameters
class RangeTuple(_RangeTupleBase):
	""" A named tuple containing range parameters.

	Attributes:
		mini     (float):        The minimum value (inclusive) (can be None if default is set)
		maxi     (float):        The maximum value (exclusive) (can be None if default is set)
		step     (float):        The step value between elements (can be None if default is set)
		default  (float|None):   Optional default value, usually middle of range

	Examples:
		>>> r = RangeTuple(mini=0.0, maxi=1.0, step=0.3)
		>>> print(r)
		mini=0.0, maxi=1.0, step=0.3, default=None
		>>> [int(x*10) for x in r]
		[0, 3, 6, 9]
		>>> len(r)
		4
		>>> r[0]
		0.0
		>>> r[100], r[99]	# High indexes will bypass the maximum value
		(30.0, 29.7)
		>>> r[1:3]
		[0.3, 0.6]
		>>> round(r[-2], 1)
		0.6
		>>> r = RangeTuple()
		Traceback (most recent call last):
			...
		ValueError: RangeTuple parameters must not be None
	"""
	def __new__(
		cls,
		mini: float | None = None,
		maxi: float | None = None,
		step: float | None = 1.0,
		default: float | None = None
	) -> RangeTuple:
		if (mini is None or maxi is None):
			if default is None:
				raise ValueError("RangeTuple parameters must not be None")
			else:
				step = None
		return super().__new__(cls, mini, maxi, step, default)

	def __str__(self) -> str:
		return f"mini={self.mini}, maxi={self.maxi}, step={self.step}, default={self.default}"

	def __repr__(self) -> str:
		return f"RangeTuple(mini={self.mini!r}, maxi={self.maxi!r}, step={self.step!r}, default={self.default!r})"

	def __iter__(self) -> Iterator[float]:
		""" Iterate over the range values.
		If the range is not initialized (mini or maxi is None), yield the default value.
		Else, yield from np.arange(...)

		Returns:
			Iterator[float]: Iterator over the range values

		Examples:
			>>> r = RangeTuple(mini=0.0, maxi=1.0, step=0.5)
			>>> list(r)
			[0.0, 0.5]
			>>> r = RangeTuple(default=1.0)
			>>> list(r)
			[1.0]
		"""
		if self.mini is None or self.maxi is None or self.step is None:
			yield self.default # type: ignore
		else:
			yield from np.arange(self.mini, self.maxi, self.step)

	def __len__(self) -> int:
		""" Return the number of values in the range.

		Returns:
			int: Number of values in the range

		Examples:
			>>> len(RangeTuple(mini=0.0, maxi=1.0, step=0.5))
			3
			>>> len(RangeTuple(default=1.0))
			1
		"""
		if self.mini is None or self.maxi is None or self.step is None:
			return 1
		else:
			return int((self.maxi - self.mini) / self.step) + 1

	def __getitem__(self, index: int | slice) -> float | list[float]:	# type: ignore
		""" Get value(s) at the given index or slice.
		If the range is not initialized, return the default value.

		Args:
			index (int | slice): Index or slice to get values for
		Returns:
			float | list[float]: Value(s) at the specified index/slice

		Examples:
			>>> r = RangeTuple(mini=0.0, maxi=1.0, step=0.5)
			>>> r[0]
			0.0
			>>> r[1]
			0.5
			>>> r[-1]
			1.0
			>>> r[0:2]
			[0.0, 0.5]
			>>> r = RangeTuple(default=1.0)
			>>> r[0]
			1.0
			>>> r[1]
			1.0
		"""
		if self.mini is None or self.maxi is None or self.step is None:
			if self.default is not None:
				return self.default
		else:
			if isinstance(index, slice):
				# Handle None values in slice by using defaults
				start: int = 0 if index.start is None else index.start
				stop: int = len(self) if index.stop is None else index.stop
				step: int = 1 if index.step is None else index.step

				return [self.mini + i * self.step for i in range(start, stop, step)]
			else:
				while index < 0:
					index = len(self) + index
				return float(self.mini + index * self.step)

	def __mul__(self, other: float) -> RangeTuple:	# type: ignore
		""" Multiply the range by a factor.

		Args:
			other (float): Factor to multiply by
		Returns:
			RangeTuple: New range with all values multiplied by the factor

		Examples:
			>>> r = RangeTuple(mini=1.0, maxi=2.0, step=0.5)
			>>> r * 2
			RangeTuple(mini=2.0, maxi=4.0, step=1.0, default=None)
			>>> r = RangeTuple(default=1.0)
			>>> r * 3
			RangeTuple(mini=None, maxi=None, step=None, default=3.0)
		"""
		return RangeTuple(
			mini=safe_multiply_none(self.mini, other),
			maxi=safe_multiply_none(self.maxi, other),
			step=safe_multiply_none(self.step, other),
			default=safe_multiply_none(self.default, other)
		)

	def __truediv__(self, other: float) -> RangeTuple:
		""" Divide the range by a factor.

		Args:
			other (float): Factor to divide by
		Returns:
			RangeTuple: New range with all values divided by the factor

		Examples:
			>>> r = RangeTuple(mini=2.0, maxi=4.0, step=1.0)
			>>> r / 2
			RangeTuple(mini=1.0, maxi=2.0, step=0.5, default=None)
			>>> r = RangeTuple(default=6.0)
			>>> r / 3
			RangeTuple(mini=None, maxi=None, step=None, default=2.0)
		"""
		return RangeTuple(
			mini=safe_divide_none(self.mini, other),
			maxi=safe_divide_none(self.maxi, other),
			step=safe_divide_none(self.step, other),
			default=safe_divide_none(self.default, other)
		)

	def random(self) -> float:
		""" Return a random value from the range.
		If the range is not initialized, return the default value.

		Returns:
			float: Random value from the range

		Examples:
			>>> r = RangeTuple(mini=0.0, maxi=1.0, step=1.0)
			>>> 0.0 <= r.random() <= 1.0
			True
			>>> r = RangeTuple(default=1.0)
			>>> r.random()
			1.0
		"""
		index: int = np.random.randint(0, len(self)) # type: ignore
		return self.__getitem__(index)  # type: ignore

