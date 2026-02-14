"""
This module provides utilities for collection manipulation:

- :py:func:`~iterable.unique_list` - Remove duplicates from a list while preserving order using object id, hash or str
- :py:func:`~iterable.at_least_n` - Check if at least n elements in an iterable satisfy a given predicate
- :py:func:`~sort_dict_keys.sort_dict_keys` - Sort dictionary keys using a given order list (ascending or descending)
- :py:func:`~dataframe.upsert_in_dataframe` - Insert or update a row in a Polars DataFrame based on primary keys
- :py:func:`~z_array.array_to_disk` - Easily handle large numpy arrays on disk using zarr for efficient storage and access.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/collections_module.gif
  :alt: stouputils collections examples
"""

# Imports
from .dataframe import *
from .iterable import *
from .sort_dict_keys import *
from .z_array import *

if __name__ == "__main__":

	# Example usage of array_to_disk (now using zarr)
	import numpy as np
	print("\nZarr Example:")
	data = np.random.rand(1000, 1000)
	zarr_array, dir_path, total_size = array_to_disk(data, delete_input=True)
	print(f"Zarr array shape: {zarr_array.shape}, directory: {dir_path}, size: {total_size:,} bytes")
	print(f"Compression ratio: {(data.nbytes / total_size):.2f}x")

	# Make it longer (1000x1000 -> 1500x1000)
	data2 = np.random.rand(500, 1000)
	longer_array, dir_path, total_size = array_to_disk(zarr_array, more_data=data2)
	print(f"\nLonger zarr array shape: {longer_array.shape}, directory: {dir_path}, size: {total_size:,} bytes")
	print(f"Compression ratio: {(1500 * 1000 * 8 / total_size):.2f}x")

