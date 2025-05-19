
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def brightness_image(image: NDArray[Any], brightness_factor: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Adjust the brightness of an image.

	Args:
		image             (NDArray[Any]):  Image to adjust brightness
		brightness_factor (float):       Brightness adjustment factor
		ignore_dtype      (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with adjusted brightness

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> brightened = brightness_image(image.astype(np.uint8), 1.5)
	>>> brightened.shape == image.shape
	True

	>>> img = np.full((3,3), 100, dtype=np.uint8)
	>>> bright = brightness_image(img, 2.0)
	>>> dark = brightness_image(img, 0.5)
	>>> bool(np.mean(bright) > np.mean(img) > np.mean(dark))
	True

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> bright_rgb = brightness_image(rgb, 1.5)
	>>> bright_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> brightness_image("not an image", 1.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> brightness_image(image.astype(np.uint8), "1.5")
	Traceback (most recent call last):
		...
	AssertionError: brightness_factor must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(brightness_factor, float | int), f"brightness_factor must be a number, got {type(brightness_factor)}"

	# Apply brightness adjustment
	return cv2.convertScaleAbs(image, alpha=brightness_factor, beta=0)

