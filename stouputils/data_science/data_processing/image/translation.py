
# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def translate_image(image: NDArray[Any], x: float, y: float, padding: int = 0, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Translate an image

	Args:
		image         (NDArray[Any]):  Image to translate
		x             (float):       Translation along the x axis (between -1 and 1)
		y             (float):       Translation along the y axis (between -1 and 1)
		padding       (int):         Padding that has been added to the image before calling this function
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Translated image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]]).astype(np.uint8)
	>>> translate_image(image, 0.5, 0.5).tolist()
	[[0, 0, 0], [0, 1, 2], [0, 4, 5]]

	>>> translate_image(image, 0, -2/3).tolist()
	[[7, 8, 9], [0, 0, 0], [0, 0, 0]]

	>>> ## Test invalid inputs
	>>> translate_image(image, 2, 0)
	Traceback (most recent call last):
		...
	AssertionError: x must be between -1 and 1, got 2

	>>> translate_image(image, 0, 2)
	Traceback (most recent call last):
		...
	AssertionError: y must be between -1 and 1, got 2

	>>> translate_image("not an image", 0, 0)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> translate_image(image, 0, 0, padding=-1)
	Traceback (most recent call last):
		...
	AssertionError: padding must be positive, got -1
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(x, float | int), f"x must be a number, got {type(x)}"
	assert isinstance(y, float | int), f"y must be a number, got {type(y)}"
	assert -1 <= x <= 1, f"x must be between -1 and 1, got {x}"
	assert -1 <= y <= 1, f"y must be between -1 and 1, got {y}"
	assert isinstance(padding, int), f"padding must be an integer, got {type(padding)}"
	assert padding >= 0, f"padding must be positive, got {padding}"

	# Get image dimensions
	height, width = image.shape[:2]
	original_width: int = width - 2 * padding
	original_height: int = height - 2 * padding

	# Convert relative translations to absolute pixels
	x_pixels: int = int(x * original_width)
	y_pixels: int = int(y * original_height)

	# Create translation matrix
	translation_matrix: NDArray[Any] = np.array([[1, 0, x_pixels], [0, 1, y_pixels]], dtype=np.float32)

	# Apply affine transformation
	return cv2.warpAffine(image, translation_matrix, (width, height))

