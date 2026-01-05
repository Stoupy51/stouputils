
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def auto_contrast_image(image: NDArray[Any], ignore_dtype: bool = False) -> NDArray[Any]:
	""" Adjust the contrast of an image.

	Args:
		image         (NDArray[Any]):  Image to adjust contrast
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with adjusted contrast

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.uint8)
	>>> adjusted = auto_contrast_image(image)
	>>> adjusted.tolist()
	[[0, 36, 73], [109, 146, 182], [219, 255, 255]]
	>>> adjusted.shape == image.shape
	True
	>>> adjusted.dtype == image.dtype
	True

	>>> ## Test invalid inputs
	>>> auto_contrast_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)

	# Perform histogram clipping
	clip_hist_percent: float = 1.0

	# Calculate the histogram of the image
	hist: NDArray[Any] = cv2.calcHist([image], [0], None, [256], [0, 256])

	# Create an accumulator list to store the cumulative histogram
	accumulator: list[float] = []
	accumulator.append(hist[0])
	for i in range(1, 256):
		accumulator.append(accumulator[i - 1] + hist[i])

	# Find the maximum value in the accumulator
	max_value: float = accumulator[-1]

	# Calculate the clipping threshold
	clip_hist_percent = clip_hist_percent * (max_value / 100.0)
	clip_hist_percent = clip_hist_percent / 2.0

	# Find the minimum and maximum gray levels after clipping
	min_gray: int = 0
	while accumulator[min_gray] < clip_hist_percent:
		min_gray = min_gray + 1
	max_gray: int = 256 - 1
	while (max_gray >= 0 and accumulator[max_gray] >= (max_value - clip_hist_percent)):
		max_gray = max_gray - 1

	# Calculate the input range after clipping
	input_range: int = max_gray - min_gray

	# If the input range is 0, return the original image
	if input_range == 0:
		return image

	# Calculate the scaling factors for contrast adjustment
	alpha: float = (256 - 1) / input_range
	beta: float = -min_gray * alpha

	# Apply the contrast adjustment
	adjusted: NDArray[Any] = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
	return adjusted

