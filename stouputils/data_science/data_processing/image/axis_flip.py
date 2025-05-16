
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from typing import Literal

from .common import Any, NDArray, check_image, cv2, np


# Functions
def flip_image(
	image: NDArray[Any], axis: Literal["horizontal", "vertical", "both"], ignore_dtype: bool = True
) -> NDArray[Any]:
	""" Flip an image along specified axis

	Args:
		image         (NDArray[Any]):     Image to flip
		axis          (str):            Axis along which to flip ("horizontal" or "vertical" or "both")
		ignore_dtype  (bool):           Ignore the dtype check
	Returns:
		NDArray[Any]: Flipped image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> flip_image(image, "horizontal").tolist()
	[[3, 2, 1], [6, 5, 4], [9, 8, 7]]

	>>> flip_image(image, "vertical").tolist()
	[[7, 8, 9], [4, 5, 6], [1, 2, 3]]

	>>> flip_image(image, "both").tolist()
	[[9, 8, 7], [6, 5, 4], [3, 2, 1]]

	>>> ## Test invalid inputs
	>>> flip_image(image, "diagonal")
	Traceback (most recent call last):
	AssertionError: axis must be either 'horizontal' or 'vertical' or 'both', got 'diagonal'

	>>> flip_image("not an image", "horizontal")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert axis in ("horizontal", "vertical", "both"), (
		f"axis must be either 'horizontal' or 'vertical' or 'both', got '{axis}'"
	)

	# Apply the flip
	if axis == "horizontal":
		return cv2.flip(image, 1)	# 1 for horizontal flip
	elif axis == "vertical":
		return cv2.flip(image, 0)	# 0 for vertical flip
	else:
		return cv2.flip(image, -1)	# -1 for both flips

