
# Imports
from PIL import Image

from .common import Any, NDArray, check_image, np


# Functions
def resize_image(
	image: NDArray[Any],
	width: int,
	height: int,
	resample: Image.Resampling | int = Image.Resampling.LANCZOS,
	ignore_dtype: bool = False
) -> NDArray[Any]:
	""" Resize an image to a new width and height.

	Args:
		image         (NDArray[Any]):              Image to resize
		width         (int):                     New width
		height        (int):                     New height
		resample      (Image.Resampling | int):  Resampling method
		ignore_dtype  (bool):                    Ignore the dtype check
	Returns:
		NDArray[Any]: Image with resized dimensions

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> resized = resize_image(image.astype(np.uint8), 6, 6)
	>>> resized.shape
	(6, 6)

	>>> img = np.ones((5, 5), dtype=np.uint8) * 255
	>>> resized = resize_image(img, 10, 10)
	>>> resized.shape
	(10, 10)

	>>> rgb = np.full((3, 3, 3), 128, dtype=np.uint8)
	>>> resized_rgb = resize_image(rgb, 6, 6)
	>>> resized_rgb.shape
	(6, 6, 3)

	>>> ## Test invalid inputs
	>>> resize_image("not an image", 10, 10)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> resize_image(image.astype(np.uint8), "10", 10)
	Traceback (most recent call last):
		...
	AssertionError: width must be integer, got <class 'str'>

	>>> resize_image(image.astype(np.uint8), 10, "10")
	Traceback (most recent call last):
		...
	AssertionError: height must be integer, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(width, int), f"width must be integer, got {type(width)}"
	assert isinstance(height, int), f"height must be integer, got {type(height)}"
	assert isinstance(resample, Image.Resampling | int), f"resample must be Image.Resampling, got {type(resample)}"

	# Resize image
	new_image: Image.Image = Image.fromarray(image)
	new_image = new_image.resize((width, height), resample=resample)
	return np.array(new_image)

