
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def sharpen_image(image: NDArray[Any], alpha: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Sharpen an image.

	Args:
		image         (NDArray[Any]):  Image to sharpen
		alpha         (float):       Sharpening factor
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Sharpened image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> sharpened = sharpen_image(image.astype(np.uint8), 1.5)
	>>> sharpened.shape == image.shape
	True

	>>> img = np.full((5,5), 128, dtype=np.uint8)
	>>> img[2,2] = 255  # Center bright pixel
	>>> sharp = sharpen_image(img, 1.0)
	>>> bool(sharp[2,2] > img[2,2] * 0.9)  # Center should stay bright
	True

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> sharp_rgb = sharpen_image(rgb, 1.0)
	>>> sharp_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> sharpen_image("not an image", 1.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> sharpen_image(image.astype(np.uint8), "1.5")
	Traceback (most recent call last):
		...
	AssertionError: alpha must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(alpha, float | int), f"alpha must be a number, got {type(alpha)}"

	# Apply sharpening
	blurred: NDArray[Any] = cv2.GaussianBlur(image, (0, 0), 3)
	return cv2.addWeighted(image, 1 + alpha, blurred, -alpha, 0)

