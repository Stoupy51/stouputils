
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from typing import Literal

from .common import Any, NDArray, check_image, cv2, np

# Constants
VALID_SPACES: list[str] = ["lab", "ycbcr", "hsv"]

# Color space conversion constants
COLOR_SPACE_CONSTANTS: dict[str, tuple[int, int, int]] = {
    "lab":    (cv2.COLOR_BGR2LAB, cv2.COLOR_LAB2BGR, 0),      # L channel index is 0
    "ycbcr":  (cv2.COLOR_BGR2YCrCb, cv2.COLOR_YCrCb2BGR, 0),  # Y channel index is 0
    "hsv":    (cv2.COLOR_BGR2HSV, cv2.COLOR_HSV2BGR, 2),      # V channel index is 2
}


# Functions
def histogram_equalization_image(
	image: NDArray[Any],
	color_space: Literal["lab", "ycbcr", "hsv"] = "lab",
	ignore_dtype: bool = False,
) -> NDArray[Any]:
	""" Apply standard histogram equalization to an image.

	Histogram equalization improves the contrast in images by stretching
	the intensity range to utilize the full range of intensity values.

	Args:
		image           (NDArray[Any]):  Image to apply histogram equalization to
		color_space     (str):           Color space to use for equalization ("lab", "ycbcr", or "hsv")
			"lab":   CIELab color space (perceptually uniform, best visual fidelity)
			"ycbcr": YCbCr color space (fast, good balance)
			"hsv":   HSV color space (intuitive, may cause color shifts)
		ignore_dtype    (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with histogram equalization applied

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> histogram_equalization_image(image.astype(np.uint8)).tolist()
	[[0, 32, 64], [96, 128, 159], [191, 223, 255]]

	>>> img = np.full((5,5), 128, dtype=np.uint8)
	>>> img[1:3, 1:3] = 200  # Create a bright region
	>>> histogram_equalization_image(img).tolist()
	[[0, 0, 0, 0, 0], [0, 255, 255, 0, 0], [0, 255, 255, 0, 0], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> rgb[1, 1, :] = 50  # Create a dark region
	>>> equalized_rgb = histogram_equalization_image(rgb)
	>>> bool(np.std(equalized_rgb) > np.std(rgb))  # Should enhance contrast
	True
	>>> equalized_rgb.tolist()
	[[[255, 255, 255], [255, 255, 255], [255, 255, 255]], [[255, 255, 255], [0, 0, 0], [255, 255, 255]], [[255, 255, 255], [255, 255, 255], [255, 255, 255]]]

	>>> ## Test each color space
	>>> test_img = np.zeros((20, 20, 3), dtype=np.uint8)
	>>> test_img[5:15, 5:15] = 200  # Add contrast region

	>>> # Test LAB color space
	>>> lab_result = histogram_equalization_image(test_img, color_space="lab")
	>>> isinstance(lab_result, np.ndarray) and lab_result.shape == test_img.shape
	True
	>>> bool(np.std(lab_result) > np.std(test_img))  # Verify contrast enhancement
	True

	>>> # Test YCbCr color space
	>>> ycbcr_result = histogram_equalization_image(test_img, color_space="ycbcr")
	>>> isinstance(ycbcr_result, np.ndarray) and ycbcr_result.shape == test_img.shape
	True
	>>> bool(np.std(ycbcr_result) > np.std(test_img))  # Verify contrast enhancement
	True

	>>> # Test HSV color space
	>>> hsv_result = histogram_equalization_image(test_img, color_space="hsv")
	>>> isinstance(hsv_result, np.ndarray) and hsv_result.shape == test_img.shape
	True
	>>> bool(np.std(hsv_result) > np.std(test_img))  # Verify contrast enhancement
	True

	>>> ## Test invalid inputs
	>>> histogram_equalization_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> histogram_equalization_image(rgb, "invalid_space")
	Traceback (most recent call last):
		...
	AssertionError: color_space must be one of: lab, ycbcr, hsv
	"""  # noqa: E501
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	lowered_color_space = color_space.lower()
	assert lowered_color_space in VALID_SPACES, f"color_space must be one of: {', '.join(VALID_SPACES)}"

	# Handle different image types
	if len(image.shape) == 2:
		# Grayscale image - just apply histogram equalization directly
		return cv2.equalizeHist(image)
	else:
		# Color image - apply equalization based on selected color space
		convert_to, convert_from, channel_idx = COLOR_SPACE_CONSTANTS[lowered_color_space]

		# Convert to target color space
		converted: NDArray[Any] = cv2.cvtColor(image, convert_to)

		# Split channels
		channels: list[NDArray[Any]] = list(cv2.split(converted))

		# Apply histogram equalization to the appropriate channel
		channels[channel_idx] = cv2.equalizeHist(channels[channel_idx])

		# Merge channels
		result: NDArray[Any] = cv2.merge(channels)

		# Convert back to BGR
		return cv2.cvtColor(result, convert_from)

