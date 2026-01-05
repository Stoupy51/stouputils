
# Imports
from .common import Any, NDArray, check_image, cv2, np


# Functions
def contrast_image(image: NDArray[Any], factor: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Adjust the contrast of an image.

	Args:
		image         (NDArray[Any]):  Image to adjust contrast
		factor        (float):       Contrast adjustment factor
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with adjusted contrast

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> contrasted = contrast_image(image.astype(np.uint8), 1.5)
	>>> contrasted.shape == image.shape
	True

	>>> img = np.array([[50, 100, 150]], dtype=np.uint8)
	>>> high = contrast_image(img, 2.0)
	>>> low = contrast_image(img, 0.5)
	>>> bool(high.std() > img.std() > low.std())  # Higher contrast = higher std
	True

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> rgb[1,1] = [50, 100, 150]
	>>> cont_rgb = contrast_image(rgb, 1.5)
	>>> cont_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> contrast_image("not an image", 1.5)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> contrast_image(image.astype(np.uint8), "1.5")
	Traceback (most recent call last):
		...
	AssertionError: factor must be a number, got <class 'str'>
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(factor, float | int), f"factor must be a number, got {type(factor)}"

	# Apply contrast adjustment
	mean: float = float(np.mean(image))
	return cv2.addWeighted(image, factor, image, 0, mean * (1 - factor))

