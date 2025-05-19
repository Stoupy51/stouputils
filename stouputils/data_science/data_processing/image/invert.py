
# Imports
from .common import Any, NDArray, check_image, np


# Function
def invert_image(image: NDArray[Any], ignore_dtype: bool = False) -> NDArray[Any]:
	""" Invert the colors of an image.

	This function inverts the colors of the input image by subtracting each pixel value
	from the maximum possible value based on the image type.

	Args:
		image         (NDArray[Any]):       Input image as a NumPy array.
		ignore_dtype  (bool):             Ignore the dtype check.
	Returns:
		NDArray[Any]: Image with inverted colors.

	>>> ## Basic tests
	>>> image = np.array([[10, 20, 30], [40, 50, 60], [70, 80, 90]], dtype=np.uint8)
	>>> inverted = invert_image(image)
	>>> inverted.tolist()
	[[245, 235, 225], [215, 205, 195], [185, 175, 165]]

	>>> # Test with floating point image
	>>> float_img = np.array([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32)
	>>> [round(float(x), 1) for x in invert_image(float_img).flatten()]
	[0.9, 0.8, 0.7, 0.6]

	>>> # Test with RGB image
	>>> rgb = np.zeros((2, 2, 3), dtype=np.uint8)
	>>> rgb[0, 0] = [255, 0, 0]  # Red pixel
	>>> inverted_rgb = invert_image(rgb)
	>>> inverted_rgb[0, 0].tolist()
	[0, 255, 255]

	>>> ## Test invalid inputs
	>>> invert_image("not an image")
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array
		"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)

	# Get the maximum value based on the image's data type
	if image.dtype == np.uint8:
		max_value = 255
	elif image.dtype == np.uint16:
		max_value = 65535
	elif image.dtype == np.float32 or image.dtype == np.float64:
		# For float images, we assume range [0, 1]
		max_value = 1.0
	else:
		# Default case, assuming 8-bit
		max_value = 255
		image = image.astype(np.uint8)

	# Invert the image
	inverted = max_value - image

	# Ensure we return the same dtype as the input
	return inverted.astype(image.dtype)

