"""
This module provides little utilities for image processing.

- :py:func:`image_resize` - Resize an image while preserving its aspect ratio by default.
- :py:func:`auto_crop` - Automatically crop an image to remove zero/uniform regions.
- :py:func:`numpy_to_gif` - Generate a '.gif' file from a 3D numpy array for visualization.
- :py:func:`numpy_to_obj` - Generate a '.obj' file from a 3D numpy array using marching cubes.
"""

# Imports
import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from .io import super_open
from .print import debug, info

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray
	from PIL import Image

# Functions
def image_resize[T: "Image.Image | NDArray[np.number]"](
	image: T,
	max_result_size: int,
	resampling: "Image.Resampling | None" = None,
	min_or_max: Callable[[int, int], int] = max,
	return_type: type[T] | str = "same",
	keep_aspect_ratio: bool = True,
) -> Any:
	""" Resize an image while preserving its aspect ratio by default.
	Scales the image so that its largest dimension equals max_result_size.

	Args:
		image             (Image.Image | NDArray):    The image to resize.
		max_result_size   (int):                      Maximum size for the largest dimension.
		resampling        (Image.Resampling | None):  PIL resampling filter to use (default: Image.Resampling.LANCZOS).
		min_or_max        (Callable):                 Function to use to get the minimum or maximum of the two ratios.
		return_type       (type | str):               Type of the return value (Image.Image, np.ndarray, or "same" to match input type).
		keep_aspect_ratio (bool):                     Whether to keep the aspect ratio.
	Returns:
		Image.Image | NDArray[np.number]: The resized image with preserved aspect ratio.
	Examples:
		>>> # Test with (height x width x channels) numpy array
		>>> import numpy as np
		>>> array = np.random.randint(0, 255, (100, 50, 3), dtype=np.uint8)
		>>> image_resize(array, 100).shape
		(100, 50, 3)
		>>> image_resize(array, 100, min_or_max=max).shape
		(100, 50, 3)
		>>> image_resize(array, 100, min_or_max=min).shape
		(200, 100, 3)

		>>> # Test with PIL Image
		>>> from PIL import Image
		>>> pil_image: Image.Image = Image.new('RGB', (200, 100))
		>>> image_resize(pil_image, 50).size
		(50, 25)
		>>> # Test with different return types
		>>> resized_array = image_resize(array, 50, return_type=np.ndarray)
		>>> isinstance(resized_array, np.ndarray)
		True
		>>> resized_array.shape
		(50, 25, 3)
		>>> # Test with different resampling methods
		>>> image_resize(pil_image, 50, resampling=Image.Resampling.NEAREST).size
		(50, 25)
	"""
	# Imports
	import numpy as np
	from PIL import Image

	# Set default resampling method if not provided
	if resampling is None:
		resampling = Image.Resampling.LANCZOS

	# Store original type for later conversion
	original_was_pil: bool = isinstance(image, Image.Image)

	# Convert numpy array to PIL Image if needed
	if not original_was_pil:
		image = Image.fromarray(image) # type: ignore

	if keep_aspect_ratio:

		# Get original image dimensions
		width: int = image.size[0]
		height: int = image.size[1]

		# Determine which dimension to use for scaling based on min_or_max function
		max_dimension: int = min_or_max(width, height)

		# Calculate scaling factor
		scale: float = max_result_size / max_dimension

		# Calculate new dimensions while preserving aspect ratio
		new_width: int = int(width * scale)
		new_height: int = int(height * scale)

		# Resize the image with the calculated dimensions
		new_image: Image.Image = image.resize((new_width, new_height), resampling)
	else:
		# If not keeping aspect ratio, resize to square with max_result_size
		new_image: Image.Image = image.resize((max_result_size, max_result_size), resampling)

	# Return the image in the requested format
	if return_type == "same":
		# Return same type as input
		if original_was_pil:
			return new_image
		else:
			return np.array(new_image)
	elif return_type != Image.Image:
		return np.array(new_image)
	else:
		return new_image


def auto_crop[T: "Image.Image | NDArray[np.number]"](
	image: T,
	mask: "NDArray[np.bool_] | None" = None,
	threshold: int | float | Callable[["NDArray[np.number]"], int | float] | None = None,
	return_type: type[T] | str = "same",
	contiguous: bool = True,
) -> Any:
	""" Automatically crop an image to remove zero or uniform regions.

	This function crops the image to keep only the region where pixels are non-zero
	(or above a threshold). It can work with a mask or directly analyze the image.

	Args:
		image       (Image.Image | NDArray):	  The image to crop.
		mask        (NDArray[bool] | None):       Optional binary mask indicating regions to keep.
		threshold   (int | float | Callable):     Threshold value or function (default: np.min).
		return_type (type | str):                 Type of the return value (Image.Image, NDArray[np.number], or "same" to match input type).
		contiguous  (bool):                       If True (default), crop to bounding box. If False, remove entire rows/columns with no content.
	Returns:
		Image.Image | NDArray[np.number]: The cropped image.

	Examples:
		>>> # Test with numpy array with zeros on edges
		>>> import numpy as np
		>>> array = np.zeros((100, 100, 3), dtype=np.uint8)
		>>> array[20:80, 30:70] = 255  # White rectangle in center
		>>> cropped = auto_crop(array, return_type=np.ndarray)
		>>> cropped.shape
		(60, 40, 3)

		>>> # Test with custom mask
		>>> mask = np.zeros((100, 100), dtype=bool)
		>>> mask[10:90, 10:90] = True
		>>> cropped_with_mask = auto_crop(array, mask=mask, return_type=np.ndarray)
		>>> cropped_with_mask.shape
		(80, 80, 3)

		>>> # Test with PIL Image
		>>> from PIL import Image
		>>> pil_image = Image.new('RGB', (100, 100), (0, 0, 0))
		>>> from PIL import ImageDraw
		>>> draw = ImageDraw.Draw(pil_image)
		>>> draw.rectangle([25, 25, 75, 75], fill=(255, 255, 255))
		>>> cropped_pil = auto_crop(pil_image)
		>>> cropped_pil.size
		(51, 51)

		>>> # Test with threshold
		>>> array_gray = np.ones((100, 100), dtype=np.uint8) * 10
		>>> array_gray[20:80, 30:70] = 255
		>>> cropped_threshold = auto_crop(array_gray, threshold=50, return_type=np.ndarray)
		>>> cropped_threshold.shape
		(60, 40)

		>>> # Test with callable threshold (using lambda to avoid min value)
		>>> array_gray2 = np.ones((100, 100), dtype=np.uint8) * 10
		>>> array_gray2[20:80, 30:70] = 255
		>>> cropped_max = auto_crop(array_gray2, threshold=lambda x: 50, return_type=np.ndarray)
		>>> cropped_max.shape
		(60, 40)

	>>> # Test with non-contiguous crop
	>>> array_sparse = np.zeros((100, 100, 3), dtype=np.uint8)
	>>> array_sparse[10, 10] = 255
	>>> array_sparse[50, 50] = 255
	>>> array_sparse[90, 90] = 255
	>>> cropped_contiguous = auto_crop(array_sparse, contiguous=True, return_type=np.ndarray)
	>>> cropped_contiguous.shape  # Bounding box from (10,10) to (90,90)
	(81, 81, 3)
	>>> cropped_non_contiguous = auto_crop(array_sparse, contiguous=False, return_type=np.ndarray)
	>>> cropped_non_contiguous.shape  # Only rows/cols 10, 50, 90
	(3, 3, 3)

	>>> # Test with 3D crop on depth dimension
	>>> array_3d = np.zeros((50, 50, 10), dtype=np.uint8)
	>>> array_3d[10:40, 10:40, 2:8] = 255  # Content only in depth slices 2-7
	>>> cropped_3d = auto_crop(array_3d, contiguous=True, return_type=np.ndarray)
	>>> cropped_3d.shape  # Should crop all 3 dimensions
	(30, 30, 6)
	"""
	# Imports
	import numpy as np
	from PIL import Image

	# Convert to numpy array and store original type
	original_was_pil: bool = isinstance(image, Image.Image)
	image_array: NDArray[np.number] = np.array(image) if original_was_pil else image # type: ignore

	# Create mask if not provided
	if mask is None:
		if threshold is None:
			threshold = cast(Callable[["NDArray[np.number]"], int | float], np.min)
		threshold_value: int | float = threshold(image_array) if callable(threshold) else threshold
		# Create a 2D mask for both 2D and 3D arrays
		if image_array.ndim == 2:
			mask = image_array > threshold_value
		else:  # 3D array
			mask = np.any(image_array > threshold_value, axis=2)

	# Find rows, columns, and depth with content
	rows_with_content: NDArray[np.bool_] = np.any(mask, axis=1)
	cols_with_content: NDArray[np.bool_] = np.any(mask, axis=0)

	# For 3D arrays, also find which depth slices have content
	depth_with_content: NDArray[np.bool_] | None = None
	if image_array.ndim == 3:
		# Create a 1D mask for depth dimension
		depth_with_content = np.any(image_array > (threshold(image_array) if callable(threshold) else threshold if threshold is not None else np.min(image_array)), axis=(0, 1))

	# Return original if no content found
	if not (np.any(rows_with_content) and np.any(cols_with_content)):
		return image_array if return_type != Image.Image else (image if original_was_pil else Image.fromarray(image_array))

	# Crop based on contiguous parameter
	if contiguous:
		row_idx, col_idx = np.where(rows_with_content)[0], np.where(cols_with_content)[0]
		if image_array.ndim == 3 and depth_with_content is not None and np.any(depth_with_content):
			depth_idx = np.where(depth_with_content)[0]
			cropped_array: NDArray[np.number] = image_array[row_idx[0]:row_idx[-1]+1, col_idx[0]:col_idx[-1]+1, depth_idx[0]:depth_idx[-1]+1]
		else:
			cropped_array: NDArray[np.number] = image_array[row_idx[0]:row_idx[-1]+1, col_idx[0]:col_idx[-1]+1]
	else:
		if image_array.ndim == 3 and depth_with_content is not None:
			# np.ix_ needs index arrays, not boolean arrays
			row_indices = np.where(rows_with_content)[0]
			col_indices = np.where(cols_with_content)[0]
			depth_indices = np.where(depth_with_content)[0]
			ix = np.ix_(row_indices, col_indices, depth_indices)
		else:
			row_indices = np.where(rows_with_content)[0]
			col_indices = np.where(cols_with_content)[0]
			ix = np.ix_(row_indices, col_indices)
		cropped_array = image_array[ix]

	# Return in requested format
	if return_type == "same":
		return Image.fromarray(cropped_array) if original_was_pil else cropped_array
	return cropped_array if return_type != Image.Image else Image.fromarray(cropped_array)


def numpy_to_gif(
	path: str,
	array: "NDArray[np.integer | np.floating | np.bool_]",
	duration: int = 100,
	loop: int = 0,
	mkdir: bool = True,
	**kwargs: Any
) -> None:
	""" Generate a '.gif' file from a numpy array for 3D/4D visualization.

	Args:
		path     (str):     Path to the output .gif file.
		array    (NDArray): Numpy array to be dumped (must be 3D or 4D).
			3D: (depth, height, width) - e.g. (64, 1024, 1024)
			4D: (depth, height, width, channels) - e.g. (50, 64, 1024, 3)
		duration (int):     Duration between frames in milliseconds.
		loop     (int):     Number of loops (0 = infinite).
		mkdir    (bool):    Create the directory if it does not exist.
		**kwargs (Any):     Additional keyword arguments for PIL.Image.save().

	Examples:

		.. code-block:: python

			> # 3D array example
			> array = np.random.randint(0, 256, (10, 100, 100), dtype=np.uint8)
			> numpy_to_gif("output_10_frames_100x100.gif", array, duration=200, loop=0)

			> # 4D array example (batch of 3D images)
			> array_4d = np.random.randint(0, 256, (5, 10, 100, 3), dtype=np.uint8)
			> numpy_to_gif("output_50_frames_100x100.gif", array_4d, duration=200)

			> total_duration = 1000  # 1 second
			> numpy_to_gif("output_1s.gif", array, duration=total_duration // len(array))
	"""
	# Imports
	import numpy as np
	from PIL import Image

	# Assertions
	assert array.ndim in (3, 4), f"The input array must be 3D or 4D, got shape {array.shape} instead."
	if array.ndim == 4:
		assert array.shape[-1] in (1, 3), f"For 4D arrays, the last dimension must be 1 or 3 (channels), got shape {array.shape} instead."

	# Create directory if needed
	if mkdir:
		dirname: str = os.path.dirname(path)
		if dirname != "":
			os.makedirs(dirname, exist_ok=True)

	# Normalize array if outside [0-255] range to [0-1]
	array = array.astype(np.float32)
	mini, maxi = np.min(array), np.max(array)
	if mini < 0 or maxi > 255:
		array = ((array - mini) / (maxi - mini + 1e-8))

	# Scale to [0-255] if in [0-1] range
	mini, maxi = np.min(array), np.max(array)
	if mini >= 0.0 and maxi <= 1.0:
		array = (array * 255)

	# Ensure array is uint8 for PIL compatibility
	array = array.astype(np.uint8)

	# Convert each slice to PIL Image
	pil_images: list[Image.Image] = [
		Image.fromarray(z_slice)
		for z_slice in array
	]

	# Save as GIF
	pil_images[0].save(
		path,
		save_all=True,
		append_images=pil_images[1:],
		duration=duration,
		loop=loop,
		**kwargs
	)


def numpy_to_obj(
	path: str,
	array: "NDArray[np.integer | np.floating | np.bool_]",
	threshold: float = 0.5,
	step_size: int = 1,
	pad_array: bool = True,
	verbose: int = 0
) -> None:
	""" Generate a '.obj' file from a numpy array for 3D visualization using marching cubes.

	Args:
		path      (str):     Path to the output .obj file.
		array     (NDArray): Numpy array to be dumped (must be 3D).
		threshold (float):   Threshold level for marching cubes (0.5 for binary data).
		step_size (int):     Step size for marching cubes (higher = simpler mesh, faster generation).
		pad_array (bool):    If True, pad array with zeros to ensure closed volumes for border cells.
		verbose   (int):     Verbosity level (0 = no output, 1 = some output, 2 = full output).

	Examples:

		.. code-block:: python

			> array = np.random.rand(64, 64, 64) > 0.5  # Binary volume
			> numpy_to_obj("output_mesh.obj", array, threshold=0.5, step_size=2, pad_array=True, verbose=1)

			> array = my_3d_data  # Some 3D numpy array (e.g. human lung scan)
			> numpy_to_obj("output_mesh.obj", array, threshold=0.3)
	"""
	# Imports
	import numpy as np
	from skimage import measure

	# Assertions
	assert array.ndim == 3, f"The input array must be 3D, got shape {array.shape} instead."
	assert step_size > 0, f"Step size must be positive, got {step_size}."
	if verbose > 1:
		debug(
			f"Generating 3D mesh from array of shape {array.shape}, "
			f"threshold={threshold}, step_size={step_size}, pad_array={pad_array}, "
			f"non-zero voxels={np.count_nonzero(array):,}"
		)

	# Convert to float for marching cubes, if needed
	volume: NDArray[np.floating] = array.astype(np.float32)
	if np.issubdtype(array.dtype, np.bool_):
		threshold = 0.5
	elif np.issubdtype(array.dtype, np.integer):
		# For integer arrays, normalize to 0-1 range
		array = array.astype(np.float32)
		min_val, max_val = np.min(array), np.max(array)
		if min_val != max_val:
			volume = (array - min_val) / (max_val - min_val)

	# Pad array with zeros to ensure closed volumes for border cells
	if pad_array:
		volume = np.pad(volume, pad_width=step_size, mode='constant', constant_values=0.0)

	# Apply marching cubes algorithm to extract mesh
	verts, faces, _, _ = cast(
        "tuple[NDArray[np.floating], NDArray[np.integer], NDArray[np.floating], NDArray[np.floating]]",
		measure.marching_cubes(volume, level=threshold, step_size=step_size, allow_degenerate=False) # type: ignore
	)

	# Shift vertices back by step_size to account for padding
	if pad_array:
		verts = verts - step_size

	if verbose > 1:
		debug(f"Generated mesh with {len(verts):,} vertices and {len(faces):,} faces")
		if step_size > 1:
			debug(f"Mesh complexity reduced by ~{step_size ** 3}x compared to step_size=1")

	# Build content using list for better performance
	content_lines: list[str] = [
		"# OBJ file generated from 3D numpy array",
		f"# Array shape: {array.shape}",
		f"# Threshold: {threshold}",
		f"# Step size: {step_size}",
		f"# Vertices: {len(verts)}",
		f"# Faces: {len(faces)}",
		""
	]

	# Add vertices
	content_lines.extend(f"v {a:.6f} {b:.6f} {c:.6f}" for a, b, c in verts)

	# Add faces (OBJ format is 1-indexed, simple format without normals)
	content_lines.extend(f"f {a+1} {b+1} {c+1}" for a, b, c in faces)

	# Write to .obj file
	with super_open(path, "w") as f:
		f.write("\n".join(content_lines) + "\n")

	if verbose > 0:
		info(f"Successfully exported 3D mesh to: '{path}'")

