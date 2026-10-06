"""
🧰 This module provides utilities for collection manipulation:

- :py:class:`~registry.Registry` - Dictionary that registers any object by decorator
- :py:func:`~iterable.unique_list` - Remove duplicates from a list while preserving order using object id, hash or str
- :py:func:`~iterable.at_least_n` - Check if at least n elements in an iterable satisfy a given predicate
- :py:func:`~sorting.sort_dict_keys` - Sort dictionary keys using a given order list (ascending or descending)
- :py:func:`~shuffle.affine_permutation_generator` - Generate a memory-efficient pseudo-random permutation of ``[0, n)``
- :py:func:`~shuffle.feistel_permutation_generator` - Memory-efficient pseudo-random permutation of ``[0, n)`` from a Feistel network
- :py:func:`~dataframe.upsert_in_dataframe` - Insert or update a row in a Polars DataFrame based on primary keys

.. code-block:: python

	import stouputils as stp

	# Remove duplicates, keeping the first occurrence of each value
	stp.info(stp.unique_list([3, 1, 3, 2, 1]))

	# Are at least 2 of these files Python files?
	def is_python_file(name: str) -> bool:
		return name.endswith(".py")

	stp.info(stp.at_least_n(["a.py", "b.txt", "c.py"], is_python_file, n=2))

	# Put the keys of a dictionary in a chosen order
	settings = {"lr": 0.1, "seed": 42, "model": "resnet"}
	stp.info(stp.sort_dict_keys(settings, order=["model", "lr", "seed"]))

	# Shuffle the numbers 0 to 9, the same way every time for a given seed
	stp.info(list(stp.affine_permutation_generator(10, seed=7)))

	# Register functions under their name, then call one by its name
	MODELS = stp.Registry()

	@MODELS.register
	def resnet() -> str:
		return "ResNet-50"

	stp.info(MODELS["resnet"]())

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/collections_module.svg
  :alt: Terminal output of the example
"""

# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from .dataframe import (
	upsert_in_dataframe as upsert_in_dataframe,
)
from .iterable import (
	at_least_n as at_least_n,
	unique_list as unique_list,
)
from .registry import (
	Registry as Registry,
)
from .shuffle import (
	FeistelHelpers as FeistelHelpers,
	affine_permutation_generator as affine_permutation_generator,
	feistel_permutation_generator as feistel_permutation_generator,
)
from .sorting import (
	sort_dict_keys as sort_dict_keys,
)

