
# Imports
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast, overload

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray
	from PIL import Image

# Type variables for overloads
T = TypeVar('T', bound="np.number | np.bool_")

# ---------------------------------------------------------------------------
# Overloads — return_offsets=False (default) — mirror original signatures
# ---------------------------------------------------------------------------

@overload
def auto_crop(
	image: "Image.Image",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	return_type: Literal["same"] = "same",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	*,
	return_offsets: Literal[False] = False,
) -> "Image.Image": ...

@overload
def auto_crop(
	image: "NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	return_type: Literal["same"] = "same",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	*,
	return_offsets: Literal[False] = False,
) -> "NDArray[T]": ...

@overload
def auto_crop(
	image: "Image.Image | NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	*,
	return_type: "type[Image.Image]",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	return_offsets: Literal[False] = False,
) -> "Image.Image": ...

@overload
def auto_crop(
	image: "Image.Image | NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	*,
	return_type: "type[np.ndarray]",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	return_offsets: Literal[False] = False,
) -> "NDArray[T]": ...


# ---------------------------------------------------------------------------
# Overloads — return_offsets=True
# ---------------------------------------------------------------------------

@overload
def auto_crop(
	image: "Image.Image",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	return_type: Literal["same"] = "same",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	*,
	return_offsets: Literal[True],
) -> "tuple[Image.Image, tuple[list[int], list[int]]]": ...

@overload
def auto_crop(
	image: "NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	return_type: Literal["same"] = "same",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	*,
	return_offsets: Literal[True],
) -> "tuple[NDArray[T], tuple[list[int], list[int]]]": ...

@overload
def auto_crop(
	image: "Image.Image | NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	*,
	return_type: "type[Image.Image]",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	return_offsets: Literal[True],
) -> "tuple[Image.Image, tuple[list[int], list[int]]]": ...

@overload
def auto_crop(
	image: "Image.Image | NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	*,
	return_type: "type[np.ndarray]",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	return_offsets: Literal[True],
) -> "tuple[NDArray[T], tuple[list[int], list[int]]]": ...


# ---------------------------------------------------------------------------
# Implementation
# ---------------------------------------------------------------------------

def auto_crop(
	image: "Image.Image | NDArray[T]",
	mask: "NDArray[np.bool_] | None" = None,
	threshold: "int | float | Callable[[NDArray[T]], int | float] | None" = None,
	return_type: "type | str" = "same",
	contiguous: bool = True,
	padding: int | tuple[int, ...] = 0,
	return_offsets: bool = False,
) -> Any:
	""" Automatically crop an image to remove zero or uniform regions.

	This function crops the image to keep only the region where pixels are non-zero
	(or above a threshold). It can work with a mask or directly analyze the image.

	Args:
		image          (Image.Image | NDArray):   The image to crop.
		mask           (NDArray[bool] | None):    Optional binary mask indicating regions to keep.
		threshold      (int | float | Callable):  Threshold value or function (default: np.min).
		return_type    (type | str):              Type of the return value (Image.Image, NDArray[np.number], or "same" to match input type).
		contiguous     (bool):                    If True (default), crop to bounding box. If False, remove entire rows/columns with no content.
		padding        (int | tuple[int, ...]):   Extra pixels/slices to keep around detected content. Use one int for all axes or one value per axis.
		return_offsets (bool):                    If True, return a tuple of (cropped_image, (lower_offsets, upper_offsets)) where
			lower_offsets and upper_offsets are lists of ints (one per axis) describing
			how many pixels were removed from each side. For non-contiguous crops, offsets
			reflect the first and last retained index on each axis.
	Returns:
		Image.Image | NDArray[np.number]:
			The cropped image when return_offsets=False (default).
		tuple[Image.Image | NDArray[np.number], tuple[list[int], list[int]]]:
			A (cropped_image, (lower_offsets, upper_offsets)) tuple when return_offsets=True.
			lower_offsets[i] is the number of leading elements removed on axis i.
			upper_offsets[i] is the number of trailing elements removed on axis i.

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

		>>> # Test return_offsets
		>>> array_off = np.zeros((20, 20), dtype=np.uint8)
		>>> array_off[5:15, 4:16] = 255
		>>> cropped_off, (lo, hi) = auto_crop(array_off, return_type=np.ndarray, return_offsets=True)
		>>> lo  # pixels removed from the top and left
		[5, 4]
		>>> hi  # pixels removed from the bottom and right
		[5, 4]

		>>> # Test return_offsets with padding
		>>> array_off_pad = np.zeros((20, 20), dtype=np.uint8)
		>>> array_off_pad[5:15, 5:15] = 255
		>>> cropped_off_pad, (lo_pad, hi_pad) = auto_crop(array_off_pad, padding=2, return_offsets=True)
		>>> lo_pad  # pixels removed from the top and left (3 instead of 5 due to padding)
		[3, 3]
		>>> hi_pad  # pixels removed from the bottom and right (3 instead of 5 due to padding)
		[3, 3]

		>>> # Test return_offsets with non-contiguous crop
		>>> array_off_nc = np.zeros((20, 20), dtype=np.uint8)
		>>> array_off_nc[5, 5] = 255
		>>> array_off_nc[10, 10] = 255
		>>> cropped_off_nc, (lo_nc, hi_nc) = auto_crop(array_off_nc, contiguous=False, return_type=np.ndarray, return_offsets=True)
		>>> lo_nc  # first retained index on each axis (5 for both)
		[5, 5]
		>>> hi_nc  # pixels removed from the end (20 - 1 - last retained index)
		[9, 9]
	"""
	# Imports
	import numpy as np
	from PIL import Image

	# Convert to numpy array and store original type
	original_was_pil: bool = isinstance(image, Image.Image)
	image_array: NDArray[T] = np.array(image) if original_was_pil else image

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
			threshold = cast(Callable[["NDArray[T]"], int | float], np.min)
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

	# Helper: build a no-content result (offsets are all zeros since nothing was removed)
	def overload_return(arr: "NDArray[T]", lower: list[int], upper: list[int]) -> Any:
		if return_type == "same":
			result: Any = Image.fromarray(arr) if original_was_pil else arr
		else:
			result = arr if return_type != Image.Image else Image.fromarray(arr)
		if return_offsets:
			return result, (lower, upper)
		return result

	# Return original if no content found
	if not (np.any(rows_with_content) and np.any(cols_with_content)):
		zeros: list[int] = [0 for _ in range(image_array.ndim)]
		return overload_return(image_array, zeros, zeros)

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

	# Crop based on contiguous parameter, tracking slice starts/ends for offsets
	lower_offsets: list[int]
	upper_offsets: list[int]

	if contiguous:
		row_idx: NDArray[np.intp] = np.where(rows_with_content)[0]
		col_idx: NDArray[np.intp] = np.where(cols_with_content)[0]
		row_start, row_end = axis_bounds(row_idx, axis=0)
		col_start, col_end = axis_bounds(col_idx, axis=1)

		if image_array.ndim == 3 and depth_with_content is not None and np.any(depth_with_content):
			depth_idx: NDArray[np.intp] = np.where(depth_with_content)[0]
			depth_start, depth_end = axis_bounds(depth_idx, axis=2)
			cropped_array: NDArray[T] = image_array[row_start:row_end, col_start:col_end, depth_start:depth_end]
			lower_offsets = [row_start, col_start, depth_start]
			upper_offsets = [image_array.shape[0] - row_end, image_array.shape[1] - col_end, image_array.shape[2] - depth_end]
		else:
			cropped_array = image_array[row_start:row_end, col_start:col_end]
			lower_offsets = [row_start, col_start]
			upper_offsets = [image_array.shape[0] - row_end, image_array.shape[1] - col_end]
			if image_array.ndim == 3:
				# depth was not cropped — offsets are zero on that axis
				lower_offsets.append(0)
				upper_offsets.append(0)
	else:
		if image_array.ndim == 3 and depth_with_content is not None:
			row_indices: NDArray[np.intp] = non_contiguous_axis_indices(rows_with_content, axis=0)
			col_indices: NDArray[np.intp] = non_contiguous_axis_indices(cols_with_content, axis=1)
			depth_indices: NDArray[np.intp] = non_contiguous_axis_indices(depth_with_content, axis=2)
			cropped_array = image_array[row_indices[:, None, None], col_indices[None, :, None], depth_indices[None, None, :]]
			lower_offsets = [int(row_indices[0]), int(col_indices[0]), int(depth_indices[0])]
			upper_offsets = [image_array.shape[0] - 1 - int(row_indices[-1]), image_array.shape[1] - 1 - int(col_indices[-1]), image_array.shape[2] - 1 - int(depth_indices[-1])]
		else:
			row_indices = non_contiguous_axis_indices(rows_with_content, axis=0)
			col_indices = non_contiguous_axis_indices(cols_with_content, axis=1)
			cropped_array = image_array[row_indices[:, None], col_indices[None, :]]
			lower_offsets = [int(row_indices[0]), int(col_indices[0])]
			upper_offsets = [image_array.shape[0] - 1 - int(row_indices[-1]), image_array.shape[1] - 1 - int(col_indices[-1])]

	return overload_return(cropped_array, lower_offsets, upper_offsets)


# Test all overloads — pyright / mypy linting
if __name__ == "__main__":
	import numpy as np
	from PIL import Image

	arr:   np.ndarray = np.zeros((100, 100, 3), dtype=np.uint8)
	arr[20:80, 30:70] = 255
	arr2d: np.ndarray = np.zeros((100, 100),    dtype=np.uint8)
	arr2d[20:80, 30:70] = 255
	pil:   Image.Image = Image.fromarray(arr)

	# ── return_offsets=False (default) ──────────────────────────────────────

	# NDArray in → NDArray out  (return_type="same" implicit)
	r1: np.ndarray   = auto_crop(arr)
	# PIL in → PIL out  (return_type="same" implicit)
	r2: Image.Image  = auto_crop(pil)
	# Any in → PIL out  (explicit return_type=Image.Image)
	r3: Image.Image  = auto_crop(arr,  return_type=Image.Image)
	r4: Image.Image  = auto_crop(pil,  return_type=Image.Image)
	# Any in → NDArray out  (explicit return_type=np.ndarray)
	r5: np.ndarray   = auto_crop(arr,  return_type=np.ndarray)
	r6: np.ndarray   = auto_crop(pil,  return_type=np.ndarray)

	# ── return_offsets=True ─────────────────────────────────────────────────
	type CropOffsets = tuple[list[int], list[int]]

	# NDArray in → (NDArray, offsets)
	r7:  tuple[np.ndarray,  CropOffsets] = auto_crop(arr,  return_offsets=True)
	# PIL in → (PIL, offsets)
	r8:  tuple[Image.Image, CropOffsets] = auto_crop(pil,  return_offsets=True)
	# Any in → (PIL, offsets)  (explicit return_type=Image.Image)
	r9:  tuple[Image.Image, CropOffsets] = auto_crop(arr,  return_type=Image.Image, return_offsets=True)
	r10: tuple[Image.Image, CropOffsets] = auto_crop(pil,  return_type=Image.Image, return_offsets=True)
	# Any in → (NDArray, offsets)  (explicit return_type=np.ndarray)
	r11: tuple[np.ndarray,  CropOffsets] = auto_crop(arr,  return_type=np.ndarray,  return_offsets=True)
	r12: tuple[np.ndarray,  CropOffsets] = auto_crop(pil,  return_type=np.ndarray,  return_offsets=True)

	# ── quick runtime sanity checks ─────────────────────────────────────────

	assert isinstance(r1, np.ndarray)  and r1.shape  == (60, 40, 3), f"unexpected shape: {r1.shape}"
	assert isinstance(r2, Image.Image) and r2.size   == (40, 60), f"unexpected size: {r2.size}"
	assert isinstance(r3, Image.Image) and r3.size   == (40, 60), f"unexpected size: {r3.size}"
	assert isinstance(r4, Image.Image) and r4.size   == (40, 60), f"unexpected size: {r4.size}"
	assert isinstance(r5, np.ndarray) and r5.shape  == (60, 40, 3), f"unexpected shape: {r5.shape}"

	cropped, (lo, hi) = r7
	assert isinstance(cropped, np.ndarray)
	assert lo == [20, 30, 0] and hi == [20, 30, 0], f"unexpected offsets: {lo=} {hi=}"

	cropped_pil, (lo2, hi2) = r8
	assert isinstance(cropped_pil, Image.Image)
	assert lo2 == [20, 30, 0] and hi2 == [20, 30, 0], f"unexpected offsets: {lo2=} {hi2=}"

	print("All overload checks passed ✓")



