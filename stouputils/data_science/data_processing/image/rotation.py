
# pyright: reportUnusedImport=false
# ruff: noqa: F401

# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def rotate_image(image: NDArray[Any], angle: float | int, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Rotate an image by a given angle.

	Args:
		image         (NDArray[Any]):  Image to rotate
		angle         (float|int):   Angle in degrees to rotate the image (between -360 and 360)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Rotated image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> rotate_image(image.astype(np.int16), 90).tolist()
	[[3, 6, 9], [2, 5, 8], [1, 4, 7]]

	>>> rotate_image(image.astype(np.float32), 90).tolist()
	[[3.0, 6.0, 9.0], [2.0, 5.0, 8.0], [1.0, 4.0, 7.0]]

	>>> rotate_image(image.astype(np.uint8), 45).tolist()
	[[1, 4, 4], [2, 5, 8], [2, 6, 5]]

	>>> rotate_image(image.astype(np.float32), 45).tolist()
	[[1.1875, 3.5625, 3.5625], [2.125, 5.0, 7.875], [2.375, 6.4375, 4.75]]

	>>> ## Test invalid inputs
	>>> rotate_image([1,2,3], 90)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> rotate_image(np.array([1,2,3]), 90)
	Traceback (most recent call last):
		...
	AssertionError: Image must have at least 2 dimensions

	>>> rotate_image(image.astype(np.uint8), "90")
	Traceback (most recent call last):
		...
	AssertionError: Angle must be a number, got <class 'str'>

	>>> rotate_image(image.astype(np.uint8), 400)
	Traceback (most recent call last):
		...
	AssertionError: Angle must be between -360 and 360 degrees, got 400

	>>> rotate_image(image.astype(np.int32), 90)
	Traceback (most recent call last):
		...
	AssertionError: Image must be of type [<class 'numpy.uint8'>, <class 'numpy.int16'>, <class 'numpy.float32'>, <class 'numpy.float64'>]
	"""  # noqa: E501
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(angle, float | int), f"Angle must be a number, got {type(angle)}"
	assert -360 <= angle <= 360, f"Angle must be between -360 and 360 degrees, got {angle}"

	# Get image dimensions
	height: int
	width: int
	height, width = image.shape[:2]
	image_center: tuple[int, int] = (width // 2, height // 2)

	# Get rotation matrix and rotate image
	rotation_matrix: NDArray[Any] = cv2.getRotationMatrix2D(image_center, angle, 1.0)
	rotated_image: NDArray[Any] = cv2.warpAffine(
		image,
		rotation_matrix,
		(width, height)
	)

	return rotated_image

