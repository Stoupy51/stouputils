
# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def shear_image(image: NDArray[Any], x: float, y: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Shear an image

	Args:
		image         (NDArray[Any]):  Image to shear
		x             (float):       Shearing along the x axis (between -180 and 180)
		y             (float):       Shearing along the y axis (between -180 and 180)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Sheared image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> shear_image(image.astype(np.uint8), 15, 0).tolist()
	[[1, 2, 3], [3, 5, 6], [3, 7, 8]]

	>>> shear_image(image.astype(np.float32), 0, 15).tolist()
	[[1.0, 1.4375, 1.40625], [4.0, 4.15625, 4.40625], [7.0, 7.15625, 7.40625]]

	>>> ## Test invalid inputs
	>>> shear_image(image.astype(np.uint8), 200, 0)
	Traceback (most recent call last):
		...
	AssertionError: x must be between -180 and 180, got 200

	>>> shear_image(image.astype(np.uint8), 0, -200)
	Traceback (most recent call last):
		...
	AssertionError: y must be between -180 and 180, got -200

	>>> shear_image("not an image", 0, 0)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(x, float | int), f"x must be a number, got {type(x)}"
	assert isinstance(y, float | int), f"y must be a number, got {type(y)}"
	assert -180 <= x <= 180, f"x must be between -180 and 180, got {x}"
	assert -180 <= y <= 180, f"y must be between -180 and 180, got {y}"

	# Get image dimensions
	height, width = image.shape[:2]

	# Convert relative shear angles to absolute values
	x_shear: float = np.tan(np.radians(x))
	y_shear: float = np.tan(np.radians(y))

	# Create shear matrix
	shear_matrix: NDArray[Any] = np.array([
		[1, x_shear, 0],
		[y_shear, 1, 0]
	], dtype=np.float32)

	# Apply affine transformation
	return cv2.warpAffine(image, shear_matrix, (width, height))

