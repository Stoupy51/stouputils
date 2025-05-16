
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def binary_threshold_image(image: NDArray[Any], threshold: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Apply binary threshold to an image.

	Args:
		image         (NDArray[Any]):  Image to threshold
		threshold     (float):       Threshold value (between 0 and 1)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Thresholded binary image

	>>> ## Basic tests
	>>> image = np.array([[100, 150, 200], [50, 125, 175], [25, 75, 225]])
	>>> binary_threshold_image(image.astype(np.uint8), 0.5).tolist()
	[[0, 255, 255], [0, 0, 255], [0, 0, 255]]

	>>> np.random.seed(42)
	>>> img = np.random.randint(0, 256, (4,4), dtype=np.uint8)
	>>> thresholded = binary_threshold_image(img, 0.7)
	>>> set(np.unique(thresholded).tolist()) <= {0, 255}  # Should only contain 0 and 255
	True

	>>> rgb = np.random.randint(0, 256, (3,3,3), dtype=np.uint8)
	>>> thresh_rgb = binary_threshold_image(rgb, 0.5)
	>>> thresh_rgb.shape == rgb.shape
	True
	>>> set(np.unique(thresh_rgb).tolist()) <= {0, 255}
	True

	>>> ## Test invalid inputs
	>>> binary_threshold_image("not an image", 0.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> binary_threshold_image(image.astype(np.uint8), "0.5")
	Traceback (most recent call last):
		...
	AssertionError: threshold must be a number, got <class 'str'>

	>>> binary_threshold_image(image.astype(np.uint8), 1.5)
	Traceback (most recent call last):
		...
	AssertionError: threshold must be between 0 and 1, got 1.5
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(threshold, float | int), f"threshold must be a number, got {type(threshold)}"
	assert 0 <= threshold <= 1, f"threshold must be between 0 and 1, got {threshold}"

	# Convert threshold from 0-1 range to 0-255 range
	threshold_value: int = int(threshold * 255)

	# Apply threshold
	if len(image.shape) == 2:
		# Grayscale image
		binary: NDArray[Any] = cv2.threshold(image, threshold_value, 255, cv2.THRESH_BINARY)[1]
	else:
		# Color image - convert to grayscale first, then back to color
		gray: NDArray[Any] = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		binary: NDArray[Any] = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)[1]
		binary = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

	return binary

