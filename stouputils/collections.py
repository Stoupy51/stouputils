"""
This module provides utilities for collection manipulation:

- unique_list: Remove duplicates from a list while preserving order using object id, hash or str
- sort_dict_keys: Sort dictionary keys using a given order list (ascending or descending)
- array_to_disk: Easily handle large numpy arrays on disk using zarr for efficient storage and access.

.. image:: https://raw.githubusercontent.com/Stoupy51/stouputils/refs/heads/main/assets/collections_module.gif
  :alt: stouputils collections examples
"""

# Imports
import atexit
import os
import shutil
import tempfile
from typing import Any, Literal, TypeVar

import numpy as np
import zarr  # pyright: ignore[reportMissingTypeStubs]
from numpy.typing import NDArray

# Typing
T = TypeVar("T")

# Functions
def unique_list(list_to_clean: list[Any], method: Literal["id", "hash", "str"] = "str") -> list[Any]:
	""" Remove duplicates from the list while keeping the order using ids (default) or hash or str

	Args:
		list_to_clean	(list[Any]):					The list to clean
		method			(Literal["id", "hash", "str"]):	The method to use to identify duplicates
	Returns:
		list[Any]: The cleaned list

	Examples:
		>>> unique_list([1, 2, 3, 2, 1], method="id")
		[1, 2, 3]

		>>> s1 = {1, 2, 3}
		>>> s2 = {2, 3, 4}
		>>> s3 = {1, 2, 3}
		>>> unique_list([s1, s2, s1, s1, s3, s2, s3], method="id")
		[{1, 2, 3}, {2, 3, 4}, {1, 2, 3}]

		>>> s1 = {1, 2, 3}
		>>> s2 = {2, 3, 4}
		>>> s3 = {1, 2, 3}
		>>> unique_list([s1, s2, s1, s1, s3, s2, s3], method="str")
		[{1, 2, 3}, {2, 3, 4}]
	"""
	# Initialize the seen ids set and the result list
	seen: set[Any] = set()
	result: list[Any] = []

	# Iterate over each item in the list
	for item in list_to_clean:
		if method == "id":
			item_identifier = id(item)
		elif method == "hash":
			item_identifier = hash(item)
		elif method == "str":
			item_identifier = str(item)
		else:
			raise ValueError(f"Invalid method: {method}")

		# If the item id is not in the seen ids set, add it to the seen ids set and append the item to the result list
		if item_identifier not in seen:
			seen.add(item_identifier)
			result.append(item)

	# Return the cleaned list
	return result

def sort_dict_keys(dictionary: dict[T, Any], order: list[T], reverse: bool = False) -> dict[T, Any]:
	""" Sort dictionary keys using a given order list (reverse optional)

	Args:
		dictionary	(dict[T, Any]):	The dictionary to sort
		order		(list[T]):		The order list
		reverse		(bool):			Whether to sort in reverse order (given to sorted function which behaves differently than order.reverse())
	Returns:
		dict[T, Any]: The sorted dictionary

	Examples:
		>>> sort_dict_keys({'b': 2, 'a': 1, 'c': 3}, order=["a", "b", "c"])
		{'a': 1, 'b': 2, 'c': 3}

		>>> sort_dict_keys({'b': 2, 'a': 1, 'c': 3}, order=["a", "b", "c"], reverse=True)
		{'c': 3, 'b': 2, 'a': 1}

		>>> sort_dict_keys({'b': 2, 'a': 1, 'c': 3, 'd': 4}, order=["c", "b"])
		{'c': 3, 'b': 2, 'a': 1, 'd': 4}
	"""
	return dict(sorted(dictionary.items(), key=lambda x: order.index(x[0]) if x[0] in order else len(order), reverse=reverse))

def array_to_disk(
	data: NDArray[Any] | zarr.Array,
	delete_input: bool = True,
	more_data: NDArray[Any] | zarr.Array | None = None
) -> tuple[zarr.Array, str, int]:
	""" Easily handle large numpy arrays on disk using zarr for efficient storage and access.

	Zarr provides a simpler and more efficient alternative to np.memmap with better compression
	and chunking capabilities.

	Args:
		data			(NDArray | zarr.Array):	The data to save/load as a zarr array
		delete_input	(bool):	Whether to delete the input data after creating the zarr array
		more_data		(NDArray | zarr.Array | None): Additional data to append to the zarr array
	Returns:
		tuple[zarr.Array, str, int]: The zarr array, the directory path, and the total size in bytes

	Examples:
		>>> data = np.random.rand(1000, 1000)
		>>> zarr_array = array_to_disk(data)[0]
		>>> zarr_array.shape
		(1000, 1000)

		>>> more_data = np.random.rand(500, 1000)
		>>> longer_array, dir_path, total_size = array_to_disk(zarr_array, more_data=more_data)
	"""
	def dir_size(directory: str) -> int:
		return sum(
			os.path.getsize(os.path.join(dirpath, filename))
			for dirpath, _, filenames in os.walk(directory)
			for filename in filenames
		)

	# If data is already a zarr.Array and more_data is present, just append and return
	if isinstance(data, zarr.Array) and more_data is not None:
		original_size: int = data.shape[0]
		new_shape: tuple[int, ...] = (original_size + more_data.shape[0], *data.shape[1:])
		data.resize(new_shape)
		data[original_size:] = more_data[:]

		# Delete more_data if specified, calculate size, and return
		if delete_input:
			del more_data
		store_path: str = str(data.store.path if hasattr(data.store, 'path') else data.store) # type: ignore
		return data, store_path, dir_size(store_path)

	# Create a temporary directory to store the zarr array (with compression (auto-chunking for optimal performance))
	temp_dir: str = tempfile.mkdtemp()
	zarr_array: zarr.Array = zarr.open_array(temp_dir, mode="w", shape=data.shape, dtype=data.dtype, chunks=True) # pyright: ignore[reportUnknownMemberType]
	zarr_array[:] = data[:]

	# If additional data is provided, resize and append
	if more_data is not None:
		original_size = data.shape[0]
		new_shape = (original_size + more_data.shape[0], *data.shape[1:])
		zarr_array.resize(new_shape)
		zarr_array[original_size:] = more_data[:]

	# Delete the original data from memory if specified
	if delete_input:
		del data
		if more_data is not None:
			del more_data

	# Register a cleanup function to delete the zarr directory at exit
	atexit.register(lambda: shutil.rmtree(temp_dir, ignore_errors=True))

	# Return all
	return zarr_array, temp_dir, dir_size(temp_dir)

if __name__ == "__main__":

	# Example usage of array_to_disk (now using zarr)
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

