
# Lazy imports (PEP 810), ignored before Python 3.15
from ..lazy import ALWAYS_LAZY

__lazy_modules__ = ALWAYS_LAZY

# Imports
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal, TypeVar, cast, overload

if TYPE_CHECKING:
	import numpy as np
	from numpy.typing import NDArray
	from PIL import Image

# Type variables for overloads
T = TypeVar('T', bound="np.number | np.bool_")
""" Any numpy numeric type, boolean included. """

# Overloads with return_offsets=False (default)

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


# Overloads with return_offsets=True

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


# Implementation

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
		image:          The image to crop.
		mask:           Optional binary mask indicating regions to keep.
		threshold:      Threshold value or function (default: np.min).
		return_type:    Type of the return value (Image.Image, NDArray[np.number], or "same" to match input type).
		contiguous:     If True (default), crop to bounding box. If False, remove entire rows/columns with no content.
		padding:        Extra pixels/slices to keep around detected content. Use one int for all axes or one value per axis.
		return_offsets: If True, return a tuple of (cropped_image, (lower_offsets, upper_offsets)) where
			lower_offsets and upper_offsets are lists of ints (one per axis) describing
			how many pixels were removed from each side. For non-contiguous crops,
			offsets reflect the first and last retained index on each axis.
	Returns:
		Image.Image | NDArray[np.number]:
			The cropped image when return_offsets=False (default).
		tuple[Image.Image | NDArray[np.number], tuple[list[int], list[int]]]:
			A (cropped_image, (lower_offsets, upper_offsets)) tuple when return_offsets=True.
			lower_offsets[i] is the number of leading elements removed on axis i.
			upper_offsets[i] is the number of trailing elements removed on axis i.
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

	# Content is what lies above the threshold, the mask (when given) deciding for rows and columns
	threshold_function = threshold if threshold is not None else cast(Callable[["NDArray[T]"], int | float], np.min)
	threshold_value: int | float = threshold_function(image_array) if callable(threshold_function) else threshold_function
	if mask is None:
		above: NDArray[np.bool_] = image_array > threshold_value
		mask = above if image_array.ndim == 2 else np.any(above, axis=2)
	contents: list[NDArray[np.bool_]] = [np.any(mask, axis=1), np.any(mask, axis=0)]

	# A 3D array also crops its depth, unless no slice holds content
	if image_array.ndim == 3:
		depth: NDArray[np.bool_] = np.any(image_array > threshold_value, axis=(0, 1))
		contents.append(depth if depth.any() else np.ones_like(depth))

	cropped, offsets = crop_to_content(image_array, contents, padding_per_axis(padding, image_array.ndim), contiguous)
	as_pil: bool = original_was_pil if return_type == "same" else return_type == Image.Image
	result: Any = Image.fromarray(cropped) if as_pil else cropped
	return (result, offsets) if return_offsets else result


def padding_per_axis(padding: int | tuple[int, ...], ndim: int) -> tuple[int, ...]:
	""" One padding value per axis, from a single value shared by all of them or a tuple already holding one each.

	>>> padding_per_axis(2, 3)
	(2, 2, 2)
	>>> padding_per_axis((1, 0), 2)
	(1, 0)
	"""
	paddings: tuple[int, ...] = (padding,) * ndim if isinstance(padding, int) else padding
	assert len(paddings) == ndim, f"padding tuple length ({len(paddings)}) must match image ndim ({ndim})"
	assert all(pad >= 0 for pad in paddings), "padding values must be >= 0"
	return paddings


def crop_to_content(
	array: "NDArray[T]", contents: "list[NDArray[np.bool_]]", padding: tuple[int, ...], contiguous: bool
) -> "tuple[NDArray[T], tuple[list[int], list[int]]]":
	""" Crop the leading axes of an array to the indices holding content, plus padding.

	Args:
		contents:   One mask per cropped axis, True where that index holds content. The array is returned whole when one is empty.
		padding:    Indices kept on each side of the content, one value per axis.
		contiguous: True keeps the padded bounding box as a view, False keeps only the padded content indices.
	Returns:
		The cropped array, and the number of indices removed before and after the kept ones on each axis.

	>>> import numpy as np
	>>> array = np.zeros((6, 6))
	>>> content = np.array([False, True, False, False, True, False])
	>>> crop_to_content(array, [content, content], (0, 1), contiguous=True)[1]
	([1, 0], [1, 0])
	>>> crop_to_content(array, [content, content], (0, 0), contiguous=False)[0].shape
	(2, 2)
	"""
	import numpy as np
	if not all(content.any() for content in contents):
		return array, ([0] * array.ndim, [0] * array.ndim)
	indices: list[NDArray[np.intp]] = [np.flatnonzero(content) for content in contents]
	if contiguous:
		bounds: list[tuple[int, int]] = [
			(max(0, int(index[0]) - pad), min(size, int(index[-1]) + 1 + pad))
			for index, size, pad in zip(indices, array.shape, padding, strict=False)
		]
		lower: list[int] = [start for start, _ in bounds]
		upper: list[int] = [size - end for (_, end), size in zip(bounds, array.shape, strict=False)]
		return array[tuple(slice(start, end) for start, end in bounds)], (lower, upper)
	kept: list[NDArray[np.intp]] = [
		np.unique(np.clip(index[:, None] + np.arange(-pad, pad + 1), 0, size - 1))
		for index, size, pad in zip(indices, array.shape, padding, strict=False)
	]
	lower = [int(index[0]) for index in kept]
	upper = [size - 1 - int(index[-1]) for index, size in zip(kept, array.shape, strict=False)]
	return array[np.ix_(*kept)], (lower, upper)


# Test all overloads - pyright / mypy linting
if __name__ == "__main__":
	import numpy as np
	from PIL import Image

	arr:   np.ndarray = np.zeros((100, 100, 3), dtype=np.uint8)
	arr[20:80, 30:70] = 255
	arr2d: np.ndarray = np.zeros((100, 100),    dtype=np.uint8)
	arr2d[20:80, 30:70] = 255
	pil:   Image.Image = Image.fromarray(arr)

	# return_offsets=False (default)

	# NDArray in -> NDArray out  (return_type="same" implicit)
	r1: np.ndarray   = auto_crop(arr)
	# PIL in -> PIL out  (return_type="same" implicit)
	r2: Image.Image  = auto_crop(pil)
	# Any in -> PIL out  (explicit return_type=Image.Image)
	r3: Image.Image  = auto_crop(arr,  return_type=Image.Image)
	r4: Image.Image  = auto_crop(pil,  return_type=Image.Image)
	# Any in -> NDArray out  (explicit return_type=np.ndarray)
	r5: np.ndarray   = auto_crop(arr,  return_type=np.ndarray)
	r6: np.ndarray   = auto_crop(pil,  return_type=np.ndarray)

	# return_offsets=True
	type CropOffsets = tuple[list[int], list[int]]

	# NDArray in -> (NDArray, offsets)
	r7:  tuple[np.ndarray,  CropOffsets] = auto_crop(arr,  return_offsets=True)
	# PIL in -> (PIL, offsets)
	r8:  tuple[Image.Image, CropOffsets] = auto_crop(pil,  return_offsets=True)
	# Any in -> (PIL, offsets)  (explicit return_type=Image.Image)
	r9:  tuple[Image.Image, CropOffsets] = auto_crop(arr,  return_type=Image.Image, return_offsets=True)
	r10: tuple[Image.Image, CropOffsets] = auto_crop(pil,  return_type=Image.Image, return_offsets=True)
	# Any in -> (NDArray, offsets)  (explicit return_type=np.ndarray)
	r11: tuple[np.ndarray,  CropOffsets] = auto_crop(arr,  return_type=np.ndarray,  return_offsets=True)
	r12: tuple[np.ndarray,  CropOffsets] = auto_crop(pil,  return_type=np.ndarray,  return_offsets=True)

	# quick runtime sanity checks

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

