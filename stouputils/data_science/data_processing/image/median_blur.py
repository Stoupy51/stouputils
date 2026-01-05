
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def median_blur_image(image: NDArray[Any], kernel_size: int = 7, iterations: int = 1) -> NDArray[Any]:
	""" Apply median blur to an image.

	Args:
		image         (NDArray[Any]):  Image to apply median blur
		kernel_size   (int):         Kernel size for the median blur
		iterations    (int):         Number of iterations for the median blur
	Returns:
		NDArray[Any]: Image with median blur applied

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.uint8)
	>>> adjusted = median_blur_image(image, kernel_size=7, iterations=1)
	>>> adjusted.tolist()
	[[3, 3, 3], [4, 5, 6], [7, 7, 7]]
	>>> adjusted.shape == image.shape
	True
	>>> adjusted.dtype == image.dtype
	True

	>>> median_blur_image(image, kernel_size=3, iterations=1).tolist()
	[[2, 3, 3], [4, 5, 6], [7, 7, 8]]
	>>> median_blur_image(image, kernel_size=3, iterations=2).tolist()
	[[3, 3, 3], [4, 5, 6], [7, 7, 7]]
	>>> median_blur_image(image, kernel_size=3, iterations=5).tolist()
	[[3, 3, 3], [4, 5, 6], [7, 7, 7]]

	>>> ## Test invalid inputs
	>>> median_blur_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array
	"""
	# Check input data
	check_image(image, ignore_dtype=True)

	# Apply median blur
	for _ in range(iterations):
		image = cv2.medianBlur(image, kernel_size)

	# Return the image
	return image

