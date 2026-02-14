
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

