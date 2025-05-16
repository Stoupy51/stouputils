
# Imports
from .common import Any, NDArray, check_image, np


# Functions
def salt_pepper_image(image: NDArray[Any], density: float, ignore_dtype: bool = False) -> NDArray[Any]:
	""" Add salt and pepper noise to an image.

	Args:
		image         (NDArray[Any]):  Image to add noise to
		density       (float):       Density of the noise (between 0 and 1)
		ignore_dtype  (bool):        Ignore the dtype check
	Returns:
		NDArray[Any]: Image with salt and pepper noise

	>>> ## Basic tests
	>>> image = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
	>>> noisy = salt_pepper_image(image.astype(np.uint8), 0.1)
	>>> noisy.shape == image.shape
	True

	>>> np.random.seed(42)
	>>> img = np.full((4,4), 128, dtype=np.uint8)
	>>> noisy = salt_pepper_image(img, 1.0)
	>>> sorted(np.unique(noisy).tolist())  # Should only contain 0 and 255
	[0, 255]

	>>> rgb = np.full((3,3,3), 128, dtype=np.uint8)
	>>> noisy_rgb = salt_pepper_image(rgb, 0.1)
	>>> noisy_rgb.shape == (3,3,3)
	True

	>>> ## Test invalid inputs
	>>> salt_pepper_image("not an image", 0.1)
	Traceback (most recent call last):
		...
	AssertionError: Image must be a numpy array

	>>> salt_pepper_image(image.astype(np.uint8), "0.1")
	Traceback (most recent call last):
		...
	AssertionError: density must be a number, got <class 'str'>

	>>> salt_pepper_image(image.astype(np.uint8), 1.5)
	Traceback (most recent call last):
		...
	AssertionError: density must be between 0 and 1, got 1.5
	"""
	# Check input data
	check_image(image, ignore_dtype=ignore_dtype)
	assert isinstance(density, float | int), f"density must be a number, got {type(density)}"
	assert 0 <= density <= 1, f"density must be between 0 and 1, got {density}"

	# Create a mask of the same shape as the input image
	mask: NDArray[Any] = np.random.choice( # pyright: ignore [reportUnknownMemberType]
		[0, 1, 2],
		size=image.shape,
		p=[1-density, density/2, density/2],
	)

	# Apply the mask to the input image
	noisy_image: NDArray[Any] = image.copy()
	noisy_image[mask == 1] = 0		# Pepper noise
	noisy_image[mask == 2] = 255	# Salt noise

	return noisy_image

