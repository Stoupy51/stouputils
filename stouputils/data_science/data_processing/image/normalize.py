
# pyright: reportUnknownVariableType=false
# pyright: reportUnusedImport=false
# pyright: reportArgumentType=false
# pyright: reportCallIssue=false

# Imports
from .common import Any, NDArray, check_image, cv2, np  # noqa: F401


# Functions
def normalize_image(
	image: NDArray[Any],
	a: float | int = 0,
	b: float | int = 255,
	method: int = cv2.NORM_MINMAX,
	ignore_dtype: bool = False,
) -> NDArray[Any]:
	""" Normalize an image to the range 0-255.

	Args:
		image         (NDArray[Any]):  Image to normalize
		a             (float | int): Minimum value (default: 0)
		b             (float | int): Maximum value (default: 255)
		method        (int):         Normalization method (default: cv2.NORM_MINMAX)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Normalized image

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=np.uint8)
	>>> normalized = normalize_image(image)
	>>> normalized.tolist()
	[[0, 32, 64], [96, 128, 159], [191, 223, 255]]
	>>> normalized.shape == image.shape
	True
	>>> normalized.dtype == image.dtype
	True

	>>> ## Test invalid inputs
	>>> normalize_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> normalize_image(image, a="not an integer")
	Traceback (most recent call last):
		...
	AssertionError: a must be a float or an integer

	>>> normalize_image(image, b="not an integer")
	Traceback (most recent call last):
		...
	AssertionError: b must be a float or an integer
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(a, float | int), "a must be a float or an integer"
	assert isinstance(b, float | int), "b must be a float or an integer"
	assert isinstance(method, int), "method must be an integer"
	assert a < b, "a must be less than b"

	# Normalize image
	return cv2.normalize(image, None, a, b, method)

