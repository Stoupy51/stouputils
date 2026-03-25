
# Imports
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray
	from PIL import Image

# Functions
def auto_crop[T: "Image.Image | NDArray[np.number]"](
	image: T,
	mask: "NDArray[np.bool_] | None" = None,
	threshold: int | float | Callable[["NDArray[np.number]"], int | float] | None = None,
	return_type: type[T] | str = "same",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
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
		padding     (int | tuple[int, ...]):      Extra pixels/slices to keep around detected content. Use one int for all axes or one value per axis.
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

		>>> # Test with padding around detected content
		>>> array_padded = np.zeros((20, 20), dtype=np.uint8)
		>>> array_padded[8:12, 8:12] = 255
		>>> cropped_padded = auto_crop(array_padded, padding=2, return_type=np.ndarray)
		>>> cropped_padded.shape
		(8, 8)
	"""
	# Imports
	import numpy as np
	from PIL import Image

	# Convert to numpy array and store original type
	original_was_pil: bool = isinstance(image, Image.Image)
	image_array: NDArray[np.number] = np.array(image) if original_was_pil else image # type: ignore

	# Normalize padding values to one entry per axis.
	if isinstance(padding, int):
		assert padding >= 0, "padding must be >= 0"
		padding_per_axis: tuple[int, ...] = tuple(padding for _ in range(image_array.ndim))
	else:
		assert len(padding) == image_array.ndim, f"padding tuple length ({len(padding)}) must match image ndim ({image_array.ndim})"
		assert all(pad >= 0 for pad in padding), "padding values must be >= 0"
		padding_per_axis = padding

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

	def axis_bounds(indices: "NDArray[np.intp]", axis: int) -> tuple[int, int]:
		""" Compute padded [start, end) bounds for one axis. """
		start: int = max(0, int(indices[0]) - padding_per_axis[axis])
		end: int = min(image_array.shape[axis], int(indices[-1]) + 1 + padding_per_axis[axis])
		return start, end

	def non_contiguous_axis_indices(content_mask: "NDArray[np.bool_]", axis: int) -> "NDArray[np.intp]":
		""" Return sparse indices for content + per-index padding for one axis. """
		indices: NDArray[np.intp] = np.where(content_mask)[0]
		pad: int = padding_per_axis[axis]
		if pad == 0:
			return indices

		candidates: list[NDArray[np.intp]] = []
		for idx in indices:
			start: int = max(0, int(idx) - pad)
			end: int = min(image_array.shape[axis], int(idx) + pad + 1)
			candidates.append(np.arange(start, end, dtype=np.intp))

		return np.unique(np.concatenate(candidates))

	# Crop based on contiguous parameter
	if contiguous:
		row_idx: NDArray[np.intp] = np.where(rows_with_content)[0]
		col_idx: NDArray[np.intp] = np.where(cols_with_content)[0]
		row_start, row_end = axis_bounds(row_idx, axis=0)
		col_start, col_end = axis_bounds(col_idx, axis=1)
		if image_array.ndim == 3 and depth_with_content is not None and np.any(depth_with_content):
			depth_idx: NDArray[np.intp] = np.where(depth_with_content)[0]
			depth_start, depth_end = axis_bounds(depth_idx, axis=2)
			cropped_array: NDArray[np.number] = image_array[row_start:row_end, col_start:col_end, depth_start:depth_end]
		else:
			cropped_array: NDArray[np.number] = image_array[row_start:row_end, col_start:col_end]
	else:
		if image_array.ndim == 3 and depth_with_content is not None:
			row_indices: NDArray[np.intp] = non_contiguous_axis_indices(rows_with_content, axis=0)
			col_indices: NDArray[np.intp] = non_contiguous_axis_indices(cols_with_content, axis=1)
			depth_indices: NDArray[np.intp] = non_contiguous_axis_indices(depth_with_content, axis=2)
			cropped_array: NDArray[np.number] = image_array[row_indices[:, None, None], col_indices[None, :, None], depth_indices[None, None, :]]
		else:
			row_indices: NDArray[np.intp] = non_contiguous_axis_indices(rows_with_content, axis=0)
			col_indices: NDArray[np.intp] = non_contiguous_axis_indices(cols_with_content, axis=1)
			cropped_array: NDArray[np.number] = image_array[row_indices[:, None], col_indices[None, :]]

	# Return in requested format
	if return_type == "same":
		return Image.fromarray(cropped_array) if original_was_pil else cropped_array
	return cropped_array if return_type != Image.Image else Image.fromarray(cropped_array)

