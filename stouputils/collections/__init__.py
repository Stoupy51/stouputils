"""
This module provides utilities for collection manipulation:

- :py:func:`~iterable.unique_list` - Remove duplicates from a list while preserving order using object id, hash or str
- :py:func:`~iterable.at_least_n` - Check if at least n elements in an iterable satisfy a given predicate
- :py:func:`~sorting.sort_dict_keys` - Sort dictionary keys using a given order list (ascending or descending)
- :py:func:`~shuffle.affine_permutation_generator` - Generate a memory-efficient pseudo-random permutation of ``[0, n)``
- :py:func:`~shuffle.feistel_permutation_generator` - Generate a memory-efficient pseudo-random permutation of ``[0, n)`` using a Feistel network
- :py:func:`~dataframe.upsert_in_dataframe` - Insert or update a row in a Polars DataFrame based on primary keys

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/collections_module.gif
  :alt: stouputils collections examples
"""

# Lazy imports (PEP 810), ignored before Python 3.15
__lazy_modules__: frozenset[str] = frozenset({
	"stouputils.collections.dataframe",
	"stouputils.collections.iterable",
	"stouputils.collections.shuffle",
	"stouputils.collections.sorting",
})

# Imports
from .dataframe import (
	upsert_in_dataframe as upsert_in_dataframe,
)
from .iterable import (
	at_least_n as at_least_n,
	unique_list as unique_list,
)
from .shuffle import (
	FeistelHelpers as FeistelHelpers,
	affine_permutation_generator as affine_permutation_generator,
	feistel_permutation_generator as feistel_permutation_generator,
)
from .sorting import (
	sort_dict_keys as sort_dict_keys,
)

