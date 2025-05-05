
# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def threshold_image(image: NDArray[Any], thresholds: list[float], ignore_dtype: bool = False) -> NDArray[Any]:
	""" Apply multi-level threshold to an image.

	Args:
		image         (NDArray[Any]):      Image to threshold
		threshold     (list[float]):     List of threshold values (between 0 and 1)
		ignore_dtype  (bool):            Ignore the dtype check
	Returns:
		NDArray[Any]: Multi-level thresholded image

	>>> ## Basic tests
	>>> image = np.array([[100, 150, 200], [50, 125, 175], [25, 75, 225]])
	>>> threshold_image(image.astype(np.uint8), [0.3, 0.6]).tolist()
	[[85, 85, 170], [0, 85, 170], [0, 0, 170]]

	>>> rgb = np.random.randint(0, 256, (3,3,3), dtype=np.uint8)
	>>> thresh_rgb = threshold_image(rgb, [0.3, 0.6])
	>>> thresh_rgb.shape == rgb.shape
	True

	>>> ## Test invalid inputs
	>>> threshold_image("not an image", [0.5])
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> threshold_image(image.astype(np.uint8), [1.5])
	Traceback (most recent call last):
		...
	AssertionError: threshold values must be between 0 and 1, got [1.5]
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert all(0 <= t <= 1 for t in thresholds), f"threshold values must be between 0 and 1, got {thresholds}"

	# Convert thresholds from 0-1 range to 0-255 range
	threshold_values: list[int] = [int(t * 255) for t in sorted(thresholds)]

	# Apply threshold
	if len(image.shape) == 2:
		# Grayscale image
		result: NDArray[Any] = np.zeros_like(image)
		for i, thresh in enumerate(threshold_values):
			value: int = int(255 * (i + 1) / (len(threshold_values) + 1))
			mask: NDArray[Any] = cv2.threshold(image, thresh, value, cv2.THRESH_BINARY)[1]
			result = cv2.max(result, mask)
	else:
		# Color image - convert to grayscale first, then back to color
		gray: NDArray[Any] = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
		result: NDArray[Any] = np.zeros_like(gray)
		for i, thresh in enumerate(threshold_values):
			value: int = int(255 * (i + 1) / (len(threshold_values) + 1))
			mask: NDArray[Any] = cv2.threshold(gray, thresh, value, cv2.THRESH_BINARY)[1]
			result = cv2.max(result, mask)
		result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

	return result

