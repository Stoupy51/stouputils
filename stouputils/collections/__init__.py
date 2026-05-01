"""
This module provides utilities for collection manipulation:

- :py:func:`~iterable.unique_list` - Remove duplicates from a list while preserving order using object id, hash or str
- :py:func:`~iterable.at_least_n` - Check if at least n elements in an iterable satisfy a given predicate
- :py:func:`~sort_dict_keys.sort_dict_keys` - Sort dictionary keys using a given order list (ascending or descending)
- :py:func:`~dataframe.upsert_in_dataframe` - Insert or update a row in a Polars DataFrame based on primary keys

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/collections_module.gif
  :alt: stouputils collections examples
"""

# Imports
from .dataframe import *
from .iterable import *
from .sort_dict_keys import *

