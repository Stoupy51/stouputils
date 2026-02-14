
# Imports
import atexit
import os
import shutil
import tempfile
from typing import TYPE_CHECKING, Any

# Lazy imports for typing
if TYPE_CHECKING:
	import zarr  # pyright: ignore[reportMissingTypeStubs]
	from numpy.typing import NDArray

# Functions
def array_to_disk(
	data: "NDArray[Any] | zarr.Array[Any]",
	delete_input: bool = True,
	more_data: "NDArray[Any] | zarr.Array[Any] | None" = None
) -> tuple["zarr.Array[Any]", str, int]:
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
		>>> import numpy as np
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

	# Imports
	try:
		import zarr  # pyright: ignore[reportMissingTypeStubs]
	except ImportError as e:
		raise ImportError("zarr is required for array_to_disk function. Please install it via 'pip install zarr'.") from e

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
	zarr_array: zarr.Array[Any] = zarr.open_array(temp_dir, mode="w", shape=data.shape, dtype=data.dtype, chunks=True) # pyright: ignore[reportUnknownMemberType]
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

