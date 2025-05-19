
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def blur_image(image: NDArray[Any], blur_strength: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Apply Gaussian blur to an image.

	Args:
		image         (NDArray[Any]):  Image to blur
		blur_strength (float):       Strength of the blur
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Blurred image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> blurred = blur_image(image.astype(np.uint8), 1.5)
	>>> blurred.shape == image.shape
	True

	>>> img = np.zeros((5,5), dtype=np.uint8)
	>>> img[2,2] = 255  # Single bright pixel
	>>> blurred = blur_image(img, 1.0)
	>>> bool(blurred[2,2] < 255)  # Center should be blurred
	True

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> blurred_rgb = blur_image(rgb, 1.0)
	>>> blurred_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> blur_image("not an image", 1.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> blur_image(image.astype(np.uint8), "1.5")
	Traceback (most recent call last):
		...
	AssertionError: blur_strength must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(blur_strength, float | int), f"blur_strength must be a number, got {type(blur_strength)}"

	# Apply Gaussian blur
	kernel_size: int = max(3, int(blur_strength * 2) + 1)
	if kernel_size % 2 == 0:
		kernel_size += 1
	blurred_image: NDArray[Any] = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)

	return blurred_image

