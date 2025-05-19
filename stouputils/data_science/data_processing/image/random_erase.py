
# pyright: reportUnknownMemberType=false

# Imports
from .common import Any, NDArray, check_image, np


# Functions
def random_erase_image(image: NDArray[Any], erase_factor: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Randomly erase a rectangle in the image.

	Args:
		image         (NDArray[Any]):  Image to apply random erase
		erase_factor  (float):       Factor determining the size of the rectangle to erase
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with random erasing applied

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> erased = random_erase_image(image.astype(np.uint8), 0.5)
	>>> erased.shape == image.shape
	True

	>>> np.random.seed(42)
	>>> img = np.ones((5,5), dtype=np.uint8) * 255
	>>> erased = random_erase_image(img, 0.4)
	>>> bool(np.any(erased == 0))  # Should have some erased pixels
	True

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> erased_rgb = random_erase_image(rgb, 0.3)
	>>> erased_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> random_erase_image("not an image", 0.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> random_erase_image(image.astype(np.uint8), "0.5")
	Traceback (most recent call last):
		...
	AssertionError: erase_factor must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(erase_factor, float | int), f"erase_factor must be a number, got {type(erase_factor)}"

	# Get image dimensions
	height, width = image.shape[:2]

	# Determine size of the rectangle to erase
	erase_height: int = int(height * erase_factor)
	erase_width: int = int(width * erase_factor)

	# Randomly choose the top-left corner of the rectangle
	top_left_x: int = np.random.randint(0, width - erase_width)
	top_left_y: int = np.random.randint(0, height - erase_height)

	# Apply random erasing
	erased_image: NDArray[Any] = image.copy()
	erased_image[top_left_y:top_left_y + erase_height, top_left_x:top_left_x + erase_width] = 0
	return erased_image

